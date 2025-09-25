import requests
from flask import current_app as app
from app import utils


def login(email, password):
    try:
        proxy_url = app.config["PROXY_URL"]
        session = requests.Session()

        response = session.get(proxy_url, timeout=app.config["REQUEST_TIMEOUT"])
        csrf_token = utils.get_csrf_token(response.text, app.config["CSRF_SCRIPT_NAME"])
        if not csrf_token:
            return None

        response = session.post(
            f"{proxy_url}{app.config['PROXY_LOGIN']}",
            json={"session": {"email": email, "password": password}},
            headers={
                "User-Agent": utils.get_user_agent(),
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": proxy_url,
            },
            timeout=app.config["REQUEST_TIMEOUT"],
        )

        if not response.ok:
            return None

        cookie = response.cookies.get(app.config["SESSION_NAME_KEY"])
        if not cookie:
            return None

        return {"cookie": cookie, "csrf_token": csrf_token}

    except Exception:
        return None


def logout(session_data):
    _request(session_data, "GET", app.config["PROXY_LOGOUT"])


def validate_session(session_data):
    response = _request(session_data, "GET", app.config["PROXY_HOME"])
    return response is not None and response.status_code != 302


def get_available_times(session_data, booking):
    club_id = app.config["CLUB_ID"]
    course_id = app.config["COURSE_ID"]
    affiliations = "&".join(
        [f"affiliation_type_ids[]={p['affiliation_id']}" for p in booking["players"]]
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
    return _request(session_data, "GET", endpoint)


def warm_session(session_data, booking, teetime_id):
    new_session_data = session_data.copy()

    def update_session_cookie(response):
        if cookie := response.cookies.get(app.config["SESSION_NAME_KEY"]):
            new_session_data["cookie"] = cookie
            return True
        return False

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

    if not (options and options.ok and update_session_cookie(options)):
        return None, None

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

    if not (response and response.ok):
        return False
    return True


def _request(session_data, method, endpoint, **kwargs):
    try:
        url = f"{app.config['PROXY_URL']}{endpoint}"
        default_headers = {
            "X-CSRF-Token": session_data["csrf_token"],
            "User-Agent": utils.get_user_agent(),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": app.config["PROXY_URL"],
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
        }

        passed_headers = kwargs.pop("headers", {})
        headers = {**default_headers, **passed_headers}

        cookies = {app.config["SESSION_NAME_KEY"]: session_data["cookie"]}
        if "timeout" not in kwargs:
            kwargs["timeout"] = app.config["REQUEST_TIMEOUT"]
        return requests.request(method, url, headers=headers, cookies=cookies, **kwargs)
    except Exception:
        app.logger.exception(f"Request failed to {endpoint}")
        return None
