from app import service as svc
from app.middlewares import require_auth
from flask import (
    Blueprint,
    request,
    jsonify,
    Response,
    stream_with_context,
    current_app,
)
import json
import queue
import threading
import time

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


@notifications_bp.route("/stream", methods=["GET"])
@require_auth
def notification_stream():
    user_id = request.user_id

    def event_stream():
        user_queue = queue.Queue()
        svc.events.add_user_queue(user_id, user_queue)

        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"

            while True:
                try:
                    event_data = user_queue.get(timeout=30)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except queue.Empty:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        finally:
            svc.events.remove_user_queue(user_id)

    response = Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Allow-Credentials": "true",
        },
    )
    return response
