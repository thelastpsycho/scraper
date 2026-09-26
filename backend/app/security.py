"""Single-operator session auth for every API endpoint.

APP_ACCESS_PIN and APP_SESSION_SECRET must be configured before the API
becomes available. Optional insecure development is restricted to an explicit
opt-in on a loopback-bound Flask server.
"""
import hmac
import os
import re
import secrets
from datetime import timedelta

from flask import jsonify, request, session

_PIN_RE = re.compile(r"^\d{6}$")


def init_security(app):
    access_pin = os.environ.get("APP_ACCESS_PIN", "")
    session_secret = os.environ.get("APP_SESSION_SECRET", "")
    dev_flag = os.environ.get("ALLOW_INSECURE_LOCAL_DEV") == "1"
    host = os.environ.get("APP_HOST", "127.0.0.1")
    dev_mode = dev_flag and host in ("127.0.0.1", "localhost", "::1") and not access_pin
    configured = (bool(_PIN_RE.match(access_pin)) and len(session_secret) >= 32 and
                  not session_secret.startswith("replace-"))
    if (access_pin or session_secret) and not configured:
        raise RuntimeError("Set APP_ACCESS_PIN to exactly 6 digits and APP_SESSION_SECRET to a random 32+ character secret; example values are invalid")

    # When unconfigured, the API is locked (not openly accessible). Health and
    # auth/status remain available to report the missing configuration.
    app.secret_key = session_secret if configured else secrets.token_urlsafe(48)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=os.environ.get("APP_SECURE_COOKIES") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    )
    app.extensions["operator_auth"] = {
        "configured": configured,
        "dev_mode": dev_mode,
        "pin": access_pin,
    }

    @app.before_request
    def secure_api():
        if not request.path.startswith("/api/"):
            return None
        if request.path in ("/api/health", "/api/auth/status", "/api/auth/login"):
            return None
        auth = app.extensions["operator_auth"]
        if auth["dev_mode"]:
            return None
        if not auth["configured"]:
            return jsonify({"status": "error", "message": "API access is not configured; set APP_ACCESS_PIN and APP_SESSION_SECRET"}), 503
        if not session.get("authenticated"):
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            actual = request.headers.get("X-CSRF-Token", "")
            expected = session.get("csrf_token", "")
            if not expected or not hmac.compare_digest(actual, expected):
                return jsonify({"status": "error", "message": "CSRF token required"}), 403
        return None


def new_csrf():
    value = secrets.token_urlsafe(32)
    session["csrf_token"] = value
    return value
