import logging
import requests
import json
from datetime import datetime, timedelta
from utils import get_payload, get_headers, get_token, desired, closest
from config import create_config_for_day
from services import ses, dynamo

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_bookings(session, config):
    affiliation = f"affiliation_type_ids[]={config.booker.affiliation_id}"
    players = "&".join([affiliation] * len(config.players))
    url = f"{config.base_url}/marketplace/clubs/{config.club_id}/teetimes?date={config.date}&course_id={config.course_id}&{players}&nb_holes={config.holes}"

    response = session.get(url)
    logger.info(f"Bookings response status: {response.status_code}")

    return response.json() if response.ok else None


def book_time(session, booking, config):
    payload = get_payload(config, "reservation", booking['id'])
    headers = get_headers(config, "reservation", config.token)
    url = f"{config.base_url}/marketplace/reservations"

    return session.post(url, json=payload, headers=headers)


def set_cookie(session, url, headers, payload=None):
    response = session.post(
        url, json=payload, headers=headers) if payload else session.get(url, headers=headers)
    if not response.ok:
        return None

    cookie = response.cookies.get_dict()['_chronogolf_session']
    session.cookies.clear()
    session.cookies.set('_chronogolf_session', cookie)
    return session


def reset_cookie(session, config, booking_id=None):
    headers = get_headers(config, "reservation", config.token)

    if booking_id is None:
        url = f"{config.base_url}/private_api/clubs/{config.club_id}/integrations"
        return set_cookie(session, url, headers)

    url = f"{config.base_url}/marketplace/reservations/options"
    payload = get_payload(config, "options", booking_id)
    return set_cookie(session, url, headers, payload)


def login(config):
    session = requests.Session()
    response = session.get(config.base_url)
    config.token = get_token(response.text)

    payload = get_payload(config, "login")
    headers = get_headers(config, "login")
    url = f"{config.base_url}/marketplace/sessions"

    return set_cookie(session, url, headers, payload)


def logout(session, base_url):
    session.get(f"{base_url}/logout")
    session.cookies.clear()


def process_booking(user_id, config):
    session = login(config)
    if not session:
        logger.error("Login failed")
        dynamo.store_booking_result(user_id, config.date, "FAILED", {
            "message": "Login failed"})
        ses.login_failed_email(config)
        return {'status': 'error', 'message': 'Login failed'}

    try:
        bookings = get_bookings(session, config)
        if not bookings:
            logger.error("No bookings found")
            dynamo.store_booking_result(user_id, config.date, "FAILED", {
                "message": "No bookings found"})
            ses.no_bookings_email(config)
            return {'status': 'error', 'message': 'No bookings found'}

        desired_bookings = [booking for booking in bookings if desired(
            booking, config.target_time)]
        if not desired_bookings:
            logger.error("No desired bookings found")
            dynamo.store_booking_result(user_id, config.date, "FAILED", {
                "message": "No desired bookings found"})
            ses.no_desired_bookings_email(config)
            return {'status': 'error', 'message': 'No desired bookings found'}

        errors = []
        for booking in sorted(desired_bookings, key=lambda b: closest(b, config.target_time)):
            if not (session := reset_cookie(session, config, booking['id'])):
                continue

            if not (session := reset_cookie(session, config)):
                continue

            response = book_time(session, booking, config)

            if response.ok:
                booking_details = {
                    'time': booking['start_time'], 'bookingId': booking['id']}
                dynamo.store_booking_result(user_id, config.date,
                                            "SUCCESS", booking_details)
                logger.info(f"Booking successful: {booking_details}")

                # Send success email notification
                ses.success_email(config, booking_details)

                return {'status': 'success', 'details': booking_details}

            errors.append(response.json().get('error', {}))

        if errors:
            error_details = {'errors': errors}
            dynamo.store_booking_result(
                user_id, config.date, "FAILED", error_details)
            logger.error(f"All booking attempts failed: {errors}")
            ses.failed_attempts_email(config, errors)
            return {'status': 'error', 'message': 'All booking attempts failed', 'errors': errors}

    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logger.error(error_msg)
        dynamo.store_booking_result(user_id, config.date, "ERROR", {
            'message': error_msg})
        ses.error_email(config, error_msg)
        return {'status': 'error', 'message': error_msg}

    finally:
        logout(session, config.base_url)
        logger.info("Booking process completed")


def lambda_handler(event, context):
    logger.info(f"Event received: {event}")

    target_date = datetime.now() + timedelta(days=5)
    target_day = target_date.strftime('%A').upper()

    logger.info(
        f"Looking for bookings for {target_day} ({target_date.date().isoformat()})")

    users = dynamo.get_all_users()
    if not users:
        logger.info("No users found in database")
        return {
            'statusCode': 200,
            'body': json.dumps("No users found")
        }

    results = []

    for user in users:
        user_id = user['userId']
        config = create_config_for_day(user, target_day, target_date.date())

        if not config:
            logger.info(f"User {user_id} has no booking for {target_day}")
            continue

        logger.info(f"Processing booking for user {user_id} on {target_day}")
        result = process_booking(user_id, config)
        results.append({
            'userId': user_id,
            'result': result
        })

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"Processed {len(results)} booking requests for {target_day}",
            'results': results
        })
    }
