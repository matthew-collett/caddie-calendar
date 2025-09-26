import queue
import threading
from typing import Dict

_notification_queues: Dict[int, queue.Queue] = {}
_notification_queues_lock = threading.Lock()


def add_user_queue(user_id: int, user_queue: queue.Queue):
    with _notification_queues_lock:
        _notification_queues[user_id] = user_queue


def remove_user_queue(user_id: int):
    with _notification_queues_lock:
        _notification_queues.pop(user_id, None)


def broadcast_notification(user_id: int, notification_data: dict):
    with _notification_queues_lock:
        user_queue = _notification_queues.get(user_id)
        if user_queue:
            try:
                user_queue.put_nowait(
                    {"type": "notification", "data": notification_data}
                )
            except queue.Full:
                pass
