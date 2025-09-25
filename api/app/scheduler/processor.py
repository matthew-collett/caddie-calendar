from datetime import date, timedelta, datetime
from concurrent.futures import ThreadPoolExecutor
from flask import current_app as app
from app import utils, service as svc
from app.cache import cache
from app.store.models import Status, NotificationType
from app.scheduler.exceptions import (
    ProcessorError,
    AuthenticationFailedError,
    NoneAvailableError,
    NoneDesiredError,
    AllFailedError,
)


def preflight():
    app.logger.info("Starting preflight job")

    try:
        target_date = date.today() + timedelta(days=5)
        pending_bookings = svc.bookings.get_bookings(
            status=Status.PENDING, booking_date=target_date
        )
        if not pending_bookings:
            app.logger.info(
                "Found no pending bookings for target date",
                extra={"date": date.today().isoformat(), "target_date": target_date},
            )
            cache.set("preflight", False)
            return
        bookings_to_cache = []
        for booking in pending_bookings:
            booking_data = booking.to_dict()
            user = svc.users.get_user_by_id(booking.user_id)
            if not user:
                app.logger.warning(
                    "Could not find user for booking",
                    extra={
                        **booking_data,
                        "date": date.today().isoformat(),
                        "target_date": target_date,
                    },
                )
                continue
            password = utils.decrypt(app.config["FERNET_KEY"], user.password_hash)

            session_data = svc.proxy.login(user.email, password)
            if session_data:
                app.sessions[user.id] = session_data
                app.logger.info(
                    "Pre-logged in user for processing", extra={"user_id": user.id}
                )

            bookings_to_cache.append(booking_data)
        cache.set("bookings", bookings_to_cache)
        cache.set("preflight", True)
        app.logger.info(
            f"Cached {len(bookings_to_cache)} bookings for processing",
            extra={"date": date.today().isoformat(), "target_date": target_date},
        )

    except Exception:
        app.logger.exception(
            "Preflight job failed",
            extra={"date": date.today().isoformat(), "target_date": target_date},
        )
        cache.set("preflight", False)


def process():
    if not cache.get("preflight"):
        app.logger.error("Preflight did not pass; Will not process")
        return

    app.logger.info("Starting process job")
    bookings = cache.get("bookings")
    if not bookings:
        app.logger.info(
            "Skipping processing; No bookings made",
            extra={"date": date.today().isoformat()},
        )
        return

    instance = app._get_current_object()

    def process_with_context(booking):
        with instance.app_context():
            process0(booking)

    with ThreadPoolExecutor(max_workers=app.config["MAX_WORKERS"]) as executor:
        executor.map(process_with_context, bookings)


def process0(booking):
    session_data = None
    try:
        user_id = booking["user_id"]
        session_data = app.sessions.get(user_id)

        if not session_data:
            raise AuthenticationFailedError

        available_times = svc.proxy.get_available_times(session_data, booking)
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
                app.logger.warning(
                    "Failure while warming session; Skipping time slot", extra=booking
                )
                continue

            success = svc.proxy.reserve(
                session_data, booking, teetime_id, rounds_attributes
            )
            if success:
                booking = svc.bookings.update_booking(
                    booking["id"],
                    {
                        "status": Status.COMPLETE,
                        "actual_time": slot["start_time"],
                        "booking_id": teetime_id,
                    },
                )
                app.logger.info(
                    "Successfully reserved time",
                    extra={
                        **booking,
                        "teetime_id": teetime_id,
                        "actual_time": slot["start_time"],
                    },
                )
                svc.notifications.create_notification(
                    user_id=booking["user_id"],
                    booking_id=booking["id"],
                    notification_type=NotificationType.BOOKING_SUCCESS,
                    title="Booking Complete!",
                    message=f"Your booking for {utils.format_date_readable(booking['booking_date'])} has been completed at {utils.format_time_12h(slot['start_time'])}.",
                )
                return

        raise AllFailedError
    except ProcessorError as e:
        handle_failure(booking, str(e))
    except Exception as e:
        handle_failure(booking, f"Unexpected error: {str(e)}")


def handle_failure(booking, error_message):
    svc.bookings.update_booking(
        booking["id"], {"status": Status.FAILED, "error_details": error_message}
    )
    app.logger.error(error_message, extra=booking, exc_info=True)
    svc.notifications.create_notification(
        user_id=booking["user_id"],
        booking_id=booking["id"],
        notification_type=NotificationType.BOOKING_FAILED,
        title="Booking Failed",
        message=f"Unfortunately, your booking for {utils.format_date_readable(booking['booking_date'])} could not be completed. Reason: {error_message}",
    )
