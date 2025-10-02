from app import service as svc
from app.middlewares import require_auth
from flask import Blueprint, jsonify, request

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/<int:user_id>", methods=["GET"])
@require_auth
def get_user_by_id(user_id):
    user = svc.users.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


@users_bp.route("", methods=["GET"])
@require_auth
def users():
    session_data = svc.sessions.get_session(request.session_id)

    name_filter = request.args.get("name_filter")
    email = request.args.get("email")

    if not name_filter and not email:
        return (
            jsonify({"error": "Either name_filter or email parameter is required"}),
            400,
        )

    users = svc.proxy.search_users(
        session_data, name_filter=name_filter, email=email
    )

    if not users:
        return jsonify({"error": "Failed to fetch users"}), 500

    return jsonify(users), 200
