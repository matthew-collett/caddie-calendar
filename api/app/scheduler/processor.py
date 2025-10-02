import threading
import time
from datetime import date, datetime, timedelta

import pytz
from app import service as svc
from app import utils
from app.cache import cache
from app.logger import get_logger
from app.scheduler.exceptions import (
    AllFailedError,
    AuthenticationFailedError,
    NoneAvailableError,
    NoneDesiredError,
    ProcessorError,
)
from app.store.models import NotificationType, Status
from flask import current_app

logger = get_logger(__name__)


def preflight(app):
    logger.info("Starting preflight job")

    try:
        svc.sessions.cleanup_expired_sessions()

        today = date.today()
        target_date = today + timedelta(days=5)
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
            cache.set("preflight", False)
            return
        bookings_to_cache = []
        sessions_to_cache = {}
        for booking in pending_bookings:
            booking_data = booking.to_dict()
            user = svc.users.get_user_by_id(booking.user_id)
            if not user:
                logger.warning(
                    "Could not find user for booking",
                    extra={
                        **booking_data,
                        "date": today.isoformat(),
                        "target_date": target_date,
                    },
                )
                continue

            user_sessions = svc.sessions.get_user_sessions(user.id)
            session_data = None
            for session in user_sessions:
                if svc.proxy.validate_session(session):
                    session_data = session
                    logger.info(
                        "Using existing valid session", extra={"user_id": user.id}
                    )
                    break

            if not session_data:
                password = utils.decrypt(app.config["FERNET_KEY"], user.password_hash)
                session_data = svc.proxy.login(user.email, password)
                if session_data:
                    svc.sessions.store_session(user.id, session_data)
                    logger.info("Created new session", extra={"user_id": user.id})

            if session_data:
                sessions_to_cache[booking_data["id"]] = session_data

            bookings_to_cache.append(booking_data)
        cache.set("bookings", bookings_to_cache)
        cache.set("sessions", sessions_to_cache)
        cache.set("preflight", True)
        logger.info(
            f"Cached {len(bookings_to_cache)} bookings for processing",
            extra={
                "date": today.isoformat(),
                "target_date": target_date.isoformat(),
            },
        )

    except Exception:
        logger.exception(
            "Preflight job failed",
            extra={
                "date": today.isoformat(),
                "target_date": target_date.isoformat(),
            },
        )
        cache.set("preflight", False)


def process(app):
    if not cache.get("preflight"):
        logger.warning("Preflight did not pass; Will not process")
        return

    logger.info("Starting process job")
    bookings = cache.get("bookings")
    if not bookings:
        today = date.today()
        logger.info(
            "Skipping processing; No bookings made",
            extra={"date": today.isoformat()},
        )
        return

    def worker(booking):
        with app.app_context():
            start_time = time.time()
            process0(booking)
            duration = time.time() - start_time
            logger.info(
                f"Booking processed in {duration:.2f} seconds",
                extra={**booking, "duration_seconds": duration},
            )

    threads = []
    for booking in bookings:
        thread = threading.Thread(target=worker, args=(booking,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def process0(booking):
    try:
        sessions = cache.get("sessions") or {}
        session_data = sessions.get(booking["id"])
        if not session_data:
            raise AuthenticationFailedError

        # Retry with exponential backoff if times aren't available yet
        available_times = None
        max_retries = 5
        for attempt in range(max_retries):
            available_times = svc.proxy.get_available_times(session_data, booking)
            if available_times:
                break
            if attempt < max_retries - 1:
                delay = (2**attempt) * 0.2  # 0.2s, 0.4s, 0.8s, 1.6s
                logger.info(
                    f"No times available, retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)

        if not available_times:
            raise NoneAvailableError

        available_slots = [
            slot for slot in available_times if utils.is_slot_available(slot)
        ]
        if not available_slots:
            raise NoneDesiredError

        available_slots.sort(
            key=lambda slot: utils.time_distance(
                slot["start_time"], booking["target_time"]
            )
        )

        for slot in available_slots:
            teetime_id = slot["id"]
            session_data, rounds_attributes = svc.proxy.warm_session(
                session_data, booking, teetime_id
            )
            if not (session_data and rounds_attributes):
                logger.warning(
                    "Failure while warming session; Skipping time slot", extra=booking
                )
                continue

            success = svc.proxy.reserve(
                session_data, booking, teetime_id, rounds_attributes
            )
            if success:
                updated_booking = svc.bookings.update_booking(
                    booking["id"],
                    {
                        "status": Status.COMPLETE,
                        "actual_time": slot["start_time"],
                        "booking_id": teetime_id,
                    },
                )
                svc.notifications.create_notification(
                    user_id=booking["user_id"],
                    booking_id=booking["id"],
                    notification_type=NotificationType.BOOKING_SUCCESS,
                    title="Booking Complete!",
                    message=f"Your booking for {utils.format_date_readable(booking['booking_date'])} has been completed at {utils.format_time_12h(slot['start_time'])}.",
                )
                logger.info(
                    "Successfully reserved time", extra=updated_booking.to_dict()
                )
                return

        raise AllFailedError
    except ProcessorError as e:
        error_msg = str(e)
        svc.bookings.update_booking(
            booking["id"], {"status": Status.FAILED, "error_details": error_msg}
        )
        logger.error(error_msg, extra=booking, exc_info=True)
        svc.notifications.create_notification(
            user_id=booking["user_id"],
            booking_id=booking["id"],
            notification_type=NotificationType.BOOKING_FAILED,
            title="Booking Failed",
            message=f"Unfortunately, your booking for {utils.format_date_readable(booking['booking_date'])} could not be completed. Reason: {error_msg}",
        )
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        svc.bookings.update_booking(
            booking["id"], {"status": Status.FAILED, "error_details": error_msg}
        )
        logger.error(error_msg, extra=booking, exc_info=True)
        svc.notifications.create_notification(
            user_id=booking["user_id"],
            booking_id=booking["id"],
            notification_type=NotificationType.BOOKING_FAILED,
            title="Booking Failed",
            message=f"Unfortunately, your booking for {utils.format_date_readable(booking['booking_date'])} could not be completed. Reason: {error_msg}",
        )
