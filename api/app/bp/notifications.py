from app import service as svc
from app.middlewares import require_auth
from flask import Blueprint, request, jsonify

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("", methods=["GET"])
@require_auth
def get_notifications():
    limit = request.args.get("limit", type=int)
    notifications = svc.notifications.get_user_notifications(request.user_id, limit)
    return jsonify([notification.to_dict() for notification in notifications]), 200


@notifications_bp.route("/unread-count", methods=["GET"])
@require_auth
def get_unread_count():
    count = svc.notifications.get_unread_count(request.user_id)
    return jsonify({"count": count}), 200


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@require_auth
def mark_notification_read(notification_id):
    success = svc.notifications.mark_as_read(notification_id, request.user_id)
    if not success:
        return jsonify({"error": "Notification not found"}), 404
    return jsonify({"message": "Notification marked as read"}), 200


