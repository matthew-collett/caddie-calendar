import threading
import time
from datetime import date, timedelta

from app import service as svc
from app import utils
from app.cache import cache
from app.logger import get_logger
from app.scheduler.exceptions import (
    AllReserveFailed,
    NoSlotsError,
    NoTimesError,
    ProcessorError,
    SessionError,
)
from app.store.models import NotificationType, Status

logger = get_logger(__name__)


def preflight(app):
    logger.info("Starting preflight job")

    today = date.today()
    target_date = today + timedelta(days=5)

    try:
        svc.sessions.cleanup_expired_sessions()
        cache.set("bookings", {})

        pending_bookings = svc.bookings.get_bookings(
            status=Status.PENDING, booking_date=target_date
        )

        if not pending_bookings:
            logger.info(
                "Found no pending bookings for target date",
                extra={
                    "date": today.isoformat(),
                    "target_date": target_date.isoformat(),
                },
            )
            return

        bookings_cache = {}

        for booking in pending_bookings:
            booking_data = booking.to_dict()
            booking_id = booking_data["id"]

            user = svc.users.get_user_by_id(booking.user_id)
            if not user:
                logger.warning("User not found", extra=booking_data)
                bookings_cache[booking_id] = {
                    "booking": booking_data,
                    "error": SessionError("User not found"),
                }
                continue

            session_data = next(
                (
                    s
                    for s in svc.sessions.get_user_sessions(user.id)
                    if svc.proxy.validate_session(s)
                ),
                None,
            )

            if session_data:
                logger.info("Using existing session", extra={"user_id": user.id})
            else:
                password = utils.decrypt(app.config["FERNET_KEY"], user.password_hash)
                session_data = svc.proxy.login(user.email, password)
                if not session_data:
                    logger.warning("Failed to create session", extra=booking_data)
                    bookings_cache[booking_id] = {
                        "booking": booking_data,
                        "error": SessionError(),
                    }
                    continue
                svc.sessions.store_session(user.id, session_data)
                logger.info("Created new session", extra={"user_id": user.id})

            times = svc.proxy.get_times(session_data, booking_data)
            if not times:
                logger.warning("No times from API", extra=booking_data)
                bookings_cache[booking_id] = {
                    "booking": booking_data,
                    "error": NoTimesError(),
                }
                continue

            available_slots = [slot for slot in times if utils.is_slot_available(slot)]
            if not available_slots:
                logger.warning("No available slots", extra=booking_data)
                bookings_cache[booking_id] = {
                    "booking": booking_data,
                    "error": NoSlotsError(),
                }
                continue

            available_slots.sort(
                key=lambda s: utils.time_distance(
                    s["start_time"], booking_data["target_time"]
                )
            )
            bookings_cache[booking_id] = {
                "booking": booking_data,
                "session": session_data,
                "times": [
                    {"id": slot["id"], "start_time": slot["start_time"]}
                    for slot in available_slots
                ],
            }

        cache.set("bookings", bookings_cache)
        logger.info(
            f"Cached {len(bookings_cache)} bookings for processing",
            extra={"date": today.isoformat(), "target_date": target_date.isoformat()},
        )

    except Exception:
        logger.exception(
            "Preflight job failed",
            extra={"date": today.isoformat(), "target_date": target_date.isoformat()},
        )


def process(app):
    logger.info("Starting process job")

    bookings_cache = cache.get("bookings")
    if not bookings_cache:
        logger.info("No bookings to process")
        return

    def worker(booking_data, error=None, session_data=None, times=None):
        with app.app_context():
            start_time = time.time()
            process0(booking_data, error, session_data, times)
            duration = time.time() - start_time
            logger.info(
                f"Booking processed in {duration:.2f} seconds",
                extra={**booking_data, "duration_seconds": duration},
            )

    threads = []
    for _, data in bookings_cache.items():
        thread = threading.Thread(
            target=worker,
            args=(
                data["booking"],
                data.get("error"),
                data.get("session"),
                data.get("times"),
            ),
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def process0(booking, error=None, session_data=None, times=None):
    def fail_booking(error_msg):
        svc.bookings.update_booking(
            booking["id"], {"status": Status.FAILED, "error_details": error_msg}
        )
        svc.notifications.create_notification(
            user_id=booking["user_id"],
            booking_id=booking["id"],
            notification_type=NotificationType.BOOKING_FAILED,
            title="Booking Failed",
            message=f"Your booking for {utils.format_date_readable(booking['booking_date'])} could not be completed. Reason: {error_msg}",
        )
        logger.error(error_msg, extra=booking, exc_info=True)

    def complete_booking(teetime_id, actual_time):
        updated_booking = svc.bookings.update_booking(
            booking["id"],
            {
                "status": Status.COMPLETE,
                "actual_time": actual_time,
                "booking_id": teetime_id,
            },
        )
        svc.notifications.create_notification(
            user_id=booking["user_id"],
            booking_id=booking["id"],
            notification_type=NotificationType.BOOKING_SUCCESS,
            title="Booking Complete!",
            message=f"Your booking for {utils.format_date_readable(booking['booking_date'])} has been completed.",
        )
        logger.info("Successfully reserved time", extra=updated_booking.to_dict())

    try:
        if error:
            raise error

        for slot in times:
            teetime_id = slot["id"]
            frozen_session = svc.proxy.freeze(session_data, teetime_id)
            if not frozen_session:
                logger.warning("Failed to freeze", extra=booking)
                continue

            warmed_session, rounds_attributes = svc.proxy.warm_session(
                frozen_session, booking, teetime_id
            )
            if not (warmed_session and rounds_attributes):
                logger.warning("warm_session failed", extra=booking)
                continue

            if svc.proxy.reserve(
                warmed_session, booking, teetime_id, rounds_attributes
            ):
                complete_booking(teetime_id, slot["start_time"])
                return

            logger.warning("reserve failed", extra=booking)

        raise AllReserveFailed

    except ProcessorError as e:
        fail_booking(str(e))
    except Exception as e:
        fail_booking(f"Unexpected error: {str(e)}")
