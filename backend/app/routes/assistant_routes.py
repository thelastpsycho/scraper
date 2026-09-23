"""Server-side proxy: never expose the DeepSeek key to browser code."""
import os

import requests
from flask import Blueprint, jsonify, request

bp = Blueprint("assistant", __name__)


@bp.route("/api/assistant/chat", methods=["POST"])
def chat():
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return jsonify({"status": "error", "message": "Assistant unavailable: configure DEEPSEEK_API_KEY on the backend"}), 503

    if request.content_length and request.content_length > 1024 * 1024:
        return jsonify({"status": "error", "message": "Assistant request is too large"}), 413

    body = request.get_json(silent=True) or {}
    messages = body.get("messages")
    if (not isinstance(messages, list) or not messages or len(messages) > 100 or
            any(not isinstance(m, dict) or m.get("role") not in ("system", "user", "assistant") or
                not isinstance(m.get("content"), str) or len(m["content"]) > 250000
                for m in messages)):
        return jsonify({"status": "error", "message": "Invalid assistant messages"}), 400
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            json={"model": "deepseek-chat", "messages": [
                {"role": m["role"], "content": m["content"]} for m in messages
            ]},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=(10, 90),
        )
        if response.status_code != 200:
            # Never relay upstream response bodies/headers (could expose details).
            return jsonify({"status": "error", "message": "Assistant service rejected the request"}), 502
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise ValueError("Assistant returned non-text content")
        return jsonify({"choices": [{"message": {"content": content}}]})
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return jsonify({"status": "error", "message": "Assistant service is temporarily unavailable"}), 502
