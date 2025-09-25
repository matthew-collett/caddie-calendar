from functools import wraps
from flask import request, jsonify, current_app as app
import jwt


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "No token provided"}), 401
        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            if payload["user_id"] not in app.sessions:
                return jsonify({"error": "Cannot find session"}), 401
            request.user_id = payload["user_id"]
            request.email = payload["email"]
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

    return decorated
