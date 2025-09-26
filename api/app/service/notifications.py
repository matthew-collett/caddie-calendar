from typing import List, Optional

from app.service import events
from app.store import db
from app.store.models import Notification, NotificationType


def create_notification(
    user_id: int,
    booking_id: int,
    notification_type: NotificationType,
    title: str,
    message: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        booking_id=booking_id,
        type=notification_type,
        title=title,
        message=message,
    )
    db.session.add(notification)
    db.session.commit()

    events.broadcast_notification(user_id, notification.to_dict())

    return notification


def get_user_notifications(
    user_id: int, limit: Optional[int] = None
) -> List[Notification]:
    query = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def get_unread_count(user_id: int) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_as_read(notification_id: int, user_id: int) -> bool:
    notification = Notification.query.filter_by(
        id=notification_id, user_id=user_id
    ).first()
    if notification:
        notification.is_read = True
        db.session.commit()
        return True
    return False
