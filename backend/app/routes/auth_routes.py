"""Session login for the local revenue console."""
import hmac

from flask import Blueprint, current_app, jsonify, request, session

from ..security import new_csrf

bp = Blueprint("auth", __name__)


@bp.route("/api/auth/status", methods=["GET"])
def status():
    conf = current_app.extensions["operator_auth"]
    authenticated = conf["dev_mode"] or (conf["configured"] and bool(session.get("authenticated")))
    result = {
        "configured": conf["configured"],
        "dev_mode": conf["dev_mode"],
        "authenticated": authenticated,
    }
    if conf["configured"] and authenticated:
        result["csrf_token"] = session.get("csrf_token") or new_csrf()
    if not conf["configured"] and not conf["dev_mode"]:
        result["message"] = "Set APP_ACCESS_PIN and APP_SESSION_SECRET on the Flask backend"
    return jsonify(result)


@bp.route("/api/auth/login", methods=["POST"])
def login():
    conf = current_app.extensions["operator_auth"]
    if not conf["configured"]:
        return jsonify({"status": "error", "message": "API authentication is not configured"}), 503
    supplied = (request.get_json(silent=True) or {}).get("pin", "")
    if not isinstance(supplied, str) or not hmac.compare_digest(supplied, conf["pin"]):
        return jsonify({"status": "error", "message": "Invalid PIN"}), 401
    session.clear()
    session.permanent = True
    session["authenticated"] = True
    return jsonify({"status": "success", "csrf_token": new_csrf()})


@bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"})
