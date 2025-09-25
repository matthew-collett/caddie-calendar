import json
from datetime import datetime
from app import store, utils
from app.store.models import Booking, Status


def create_booking(user_id, booking_data):
    booking = Booking(
        user_id=user_id,
        booking_date=datetime.strptime(booking_data["booking_date"], "%Y-%m-%d").date(),
        target_time=datetime.strptime(booking_data["target_time"], "%H:%M:%S").time(),
        holes=booking_data["holes"],
        players=json.dumps(booking_data["players"]),
    )

    store.add(booking)
    store.commit()
    return booking


def get_bookings(status, booking_date):
    return Booking.query.filter_by(status=status, booking_date=booking_date).all()


def get_user_bookings(user_id):
    return Booking.query.filter_by(user_id=user_id).all()


def get_booking(booking_id):
    return Booking.query.get(booking_id)


def get_particpating_bookings(user_id):
    bookings = Booking.query.filter(Booking.user_id != user_id).all()
    user_bookings = []

    for booking in bookings:
        players_data = json.loads(booking.players) if booking.players else []
        if any(player["user_id"] == user_id for player in players_data):
            user_bookings.append(booking)

    return user_bookings


def update_booking(booking_id, update_data):
    booking = Booking.query.get(booking_id)
    if not booking:
        return None

    if "actual_time" in update_data:
        update_data["actual_time"] = datetime.strptime(
            update_data["actual_time"], "%H:%M"
        ).time()

    if "status" in update_data:
        if isinstance(update_data["status"], str):
            update_data["status"] = Status(update_data["status"])

    for key, value in update_data.items():
        if hasattr(booking, key):
            setattr(booking, key, value)

    booking.updated_at = utils.ensure_utc_now()

    store.commit()
    return booking


def delete_booking(booking_id, user_id):
    booking = Booking.query.get(booking_id)
    if not booking or booking.user_id != user_id:
        return False

    store.delete(booking)
    store.commit()
    return True
