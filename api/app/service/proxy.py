from urllib.parse import unquote

from curl_cffi import requests
from app import utils
from app.logger import get_logger
from flask import current_app as app

logger = get_logger(__name__)


def login(email, password):
    try:
        proxy_url = app.config["PROXY_URL"]
        session = requests.Session()

        logger.info("[Proxy Request] GET /")
        response = session.get(
            proxy_url,
            timeout=app.config["REQUEST_TIMEOUT"],
            impersonate="firefox133"
        )
        logger.info(
            f"[Proxy Request] GET / - Status: {response.status_code}, Length: {len(response.text)}"
        )

        if not response.ok:
            logger.error(
                f"[Proxy Request] GET / - HTTP {response.status_code}: {response.text[:1000]}"
            )
            return None

        csrf_token = utils.get_csrf_token(response.text, app.config["CSRF_SCRIPT_NAME"])
        if not csrf_token:
            return None

        endpoint = app.config['PROXY_LOGIN']
        logger.info(f"[Proxy Request] POST {endpoint}")
        response = session.post(
            f"{proxy_url}{endpoint}",
            json={"session": {"email": email, "password": password}},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": proxy_url,
            },
            timeout=app.config["REQUEST_TIMEOUT"],
            impersonate="firefox133"
        )
        logger.info(
            f"[Proxy Request] POST {endpoint} - Status: {response.status_code}, Length: {len(response.text)}"
        )

        if not response.ok:
            logger.error(
                f"[Proxy Request] POST {endpoint} - HTTP {response.status_code}: {response.text[:1000]}"
            )
            return None

        return {"cookies": dict(session.cookies), "csrf_token": csrf_token}

    except Exception:
        logger.exception(f"[Proxy Request] POST {app.config['PROXY_LOGIN']}")
        return None


def logout(session_data):
    _request(session_data, "GET", app.config["PROXY_LOGOUT"])


def validate_session(session_data):
    response = _request(session_data, "GET", app.config["PROXY_LOGIN"])
    return response is not None and response.status_code == 200


def get_available_times(session_data, booking):
    club_id = app.config["CLUB_ID"]
    course_id = app.config["COURSE_ID"]

    owner_affiliation_id = next(
        p["affiliation_id"] for p in booking["players"] if p["user_id"] == booking["user_id"]
    )
    affiliations = "&".join(
        [f"affiliation_type_ids[]={owner_affiliation_id}"] * len(booking["players"])
    )

    endpoint = f"{app.config["PROXY_SEARCH"].format(club_id=club_id)}?date={booking['booking_date']}&course_id={course_id}&{affiliations}&nb_holes={booking['holes']}"
    response = _request(session_data, "GET", endpoint)
    return response.json() if response and response.ok else None


def search_users(session_data, name_filter=None, email=None):
    club_id = app.config["CLUB_ID"]
    if email:
        q = f"(user.email:${email})"
    elif name_filter:
        query_parts = [
            f"user.full_name:{part.lower()}*" for part in name_filter.split()
        ]
        q = f"({' AND '.join(query_parts)})"
    else:
        return None

    endpoint = (
        f"{app.config['PROXY_PEOPLE'].format(club_id=club_id)}?club_id={club_id}&q={q}"
    )
    response = _request(session_data, "GET", endpoint)
    return response.json() if response and response.ok else None


def warm_session(session_data, booking, teetime_id):
    new_session_data = {
        "cookies": session_data["cookies"].copy(),
        "csrf_token": session_data["csrf_token"]
    }

    options = _request(
        new_session_data,
        "POST",
        f"{app.config["PROXY_RESERVE"]}/options",
        json={
            "medium": "dashboard",
            "nb_holes": booking["holes"],
            "source": app.config["SOURCE"],
            "teetime_id": teetime_id,
            "rounds_attributes": [
                {
                    "affiliation_type_id": player["affiliation_id"],
                    "extras": [],
                    "discounts": [],
                }
                for player in booking["players"]
            ],
        },
    )

    if not (options and options.ok):
        return None, None

    new_session_data["cookies"].update(options.cookies)

    try:
        rounds_attributes = []
        for i, round_data in enumerate(options.json()[0]["rounds"]):
            round_lines = round_data["round_lines"][0]

            rounds_attributes.append(
                {
                    "id": None,
                    "affiliation_type_id": round_data["affiliation_type_id"],
                    "guest": None,
                    "reservation_id": None,
                    "state": "reserved",
                    "raincheck_issued_at": None,
                    "user_id": booking["players"][i]["user_id"],
                    "cancelled_at": None,
                    "requires_payment": round_data["requires_payment"],
                    "check_in_medium": None,
                    "check_in_kiosk_id": None,
                    "checked_in_at": None,
                    "fully_refunded": False,
                    "round_lines_attributes": [
                        {
                            "id": None,
                            "round_id": None,
                            "discount_id": None,
                            "discount_rule_id": None,
                            "kit_id": None,
                            "kit_reference": None,
                            "product_id": round_lines["product_id"],
                            "product_rule_id": round_lines["product_rule_id"],
                            "original_unit_price": round_lines["original_unit_price"],
                            "unit_price": round_lines["unit_price"],
                            "quantity": 1,
                            "refunded_at": None,
                            "refundable": False,
                            "unit_quantity": 1,
                        }
                    ],
                }
            )

        return new_session_data, rounds_attributes
    except (IndexError, KeyError, TypeError):
        return None, None


def reserve(session_data, booking, teetime_id, rounds_attributes):
    response = _request(
        session_data,
        "POST",
        app.config["PROXY_RESERVE"],
        json={
            "reservation": {
                "club_id": app.config["CLUB_ID"],
                "teetime_id": teetime_id,
                "recurrence_id": None,
                "state": "confirmed",
                "holes": booking["holes"],
                "eligible_for_mobile_self_check_in": False,
                "made_online": True,
                "origin_reservation_id": None,
                "created_user_id": None,
                "reminder_chronodeal_chosen_at": None,
                "source": app.config["SOURCE"],
                "online_note": "\n".join(
                    [p["note"] for p in booking["players"] if p.get("note")]
                ),
                "booking_reference": None,
                "cancellable": True,
                "editable": True,
                "force_online_payment": False,
                "discount_type": None,
                "club": {
                    "id": app.config["CLUB_ID"],
                    "name": app.config["CLUB_NAME"],
                    "currency_code": "CAD",
                },
                "lottery_choices_attributes": None,
                "rounds_attributes": rounds_attributes,
                "payment_source_id": None,
                "payment_source_type": None,
                "medium": "dashboard",
                "booking_engine": 1,
            }
        },
        headers={"Referer": app.config["PROXY_REFERER"]},
    )

    return response is not None and response.ok


def _request(session_data, method, endpoint, **kwargs):
    url = f"{app.config['PROXY_URL']}{endpoint}"

    try:
        default_headers = {
            "X-CSRF-Token": session_data["csrf_token"],
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": f"{app.config['PROXY_URL']}/dashboard/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Priority": "u=0",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        headers = {**default_headers, **kwargs.pop("headers", {})}

        cookies = session_data["cookies"]
        if "timeout" not in kwargs:
            kwargs["timeout"] = app.config["REQUEST_TIMEOUT"]

        logger.info(f"[Proxy Request] {method} {endpoint}")
        response = requests.request(
            method, url, headers=headers, cookies=cookies, impersonate="firefox133", **kwargs
        )
        logger.info(
            f"[Proxy Request] {method} {endpoint} - Status: {response.status_code}, Length: {len(response.text)}"
        )

        if not response.ok:
            logger.error(
                f"[Proxy Request] {method} {endpoint} - HTTP {response.status_code}: {response.text[:1000]}"
            )

        return response
    except Exception:
        logger.exception(f"[Proxy Request] {method} {endpoint}")
        return None
