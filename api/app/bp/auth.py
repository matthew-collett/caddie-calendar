import jwt
from app import utils, service as svc
from app.middlewares import require_auth
from flask import Blueprint, request, jsonify, current_app as app
from datetime import datetime, timedelta, timezone


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    email = data["email"]
    password = data["password"]

    user = svc.users.get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 401

    stored_password = utils.decrypt(app.config["FERNET_KEY"], user.password_hash)
    if stored_password != password:
        return jsonify({"error": "Invalid email or password"}), 401

    session_data = svc.proxy.login(email, password)
    if session_data is None:
        return jsonify({"error": "Login failed"}), 401

    svc.sessions.store_session(user.id, session_data)

    token = jwt.encode(
        {
            "user_id": user.id,
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    return jsonify({"token": token, "expires_in": 3600}), 200


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    user_id = request.user_id
    session_data = svc.sessions.get_session(user_id)
    if session_data:
        svc.proxy.logout(session_data)
    svc.sessions.delete_session(user_id)
    return jsonify({"success": True}), 200


@auth_bp.route("/status", methods=["GET"])
@require_auth
def status():
    user_id = request.user_id
    session_data = svc.sessions.get_session(user_id)
    valid = svc.proxy.validate_session(session_data)
    if not valid:
        logout()
    return jsonify({"auth": valid}), 200
