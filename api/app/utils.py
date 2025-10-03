import json
import re
from datetime import datetime, timezone

from cryptography.fernet import Fernet


def encrypt(key, password):
    return Fernet(key).encrypt(password.encode("utf-8"))


def decrypt(key, password):
    return Fernet(key).decrypt(password).decode("utf-8")


def get_csrf_token(html, script_name):
    pattern = rf"{re.escape(script_name)}\s*=\s*(\{{.*?\}})(?:;|\s)"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return None

    try:
        config = json.loads(match.group(1))
        return config.get("CSRF_TOKEN")
    except json.JSONDecodeError:
        return None


def is_slot_available(slot):
    return not slot.get("out_of_capacity", True)


def time_distance(slot_time, target_time):
    return abs(minutes(slot_time) - minutes(target_time))


def minutes(time_str):
    time_parts = time_str.split(":")
    return int(time_parts[0]) * 60 + int(time_parts[1])


def to_utc_datetime(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def serialize_datetime(dt):
    if dt is None:
        return None
    utc_dt = to_utc_datetime(dt)
    return utc_dt.isoformat()


def serialize_date(d):
    if d is None:
        return None
    return d.isoformat()


def serialize_time(t):
    if t is None:
        return None
    return t.isoformat()


def ensure_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_date_readable(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%a, %b %d")


def format_time_12h(time_str):
    time_obj = datetime.strptime(time_str, "%H:%M")
    return time_obj.strftime("%I:%M %p").lstrip("0")
