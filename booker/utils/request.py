import json
from utils import decrypt


def load_file(template_path):
    with open(template_path, 'r') as file:
        return file.read()


def get_payload(config, type, booking_id=None):
    if type == "login":
        return login_payload(config)
    elif type == "options":
        return options_payload(config, booking_id)
    else:
        return reservation_payload(config, booking_id)


def get_headers(config, type, token=None):
    return login_headers(config) if type == "login" else reservation_headers(config, token)


def login_payload(config):
    return {
        "session": {
            "email": config.email,
            "password": decrypt(config.fernet_key, config.password)
        }
    }


def options_payload(config, booking_id):
    payload = {
        "medium": "dashboard",
        "nb_holes": config.holes,
        "source": "chronogolf",
        "teetime_id": booking_id,
        "rounds_attributes": []
    }
    for player in config.players:
        round_attribute = {
            "affiliation_type_id": player.affiliation_id,
            "discounts": [],
            "extras": []
        }
        payload['rounds_attributes'].append(round_attribute)
    return payload


def reservation_payload(config, booking_id):
    template = load_file('templates/reservation_template.json')
    template = template.replace('{{CLUB_ID}}', str(config.club_id))
    template = template.replace('{{TEETIME_ID}}', str(booking_id))
    template = template.replace('{{HOLES}}', str(config.holes))
    template = template.replace('{{CLUB_NAME}}', config.club_name)
    template = template.replace('{{CURRENCY_CODE}}', config.currency_code)

    payload = json.loads(template)

    for player in config.players:
        round_attribute = {
            "id": None,
            "affiliation_type_id": player.affiliation_id,
            "guest": None,
            "reservation_id": None,
            "state": "reserved",
            "raincheck_issued_at": None,
            "user_id": player.user_id,
            "cancelled_at": None,
            "requires_payment": False,
            "check_in_medium": None,
            "check_in_kiosk_id": None,
            "checked_in_at": None,
            "fully_refunded": False,
            "round_lines_attributes": [
                {
                    "discount_id": None,
                    "discount_rule_id": None,
                    "id": None,
                    "kit_id": None,
                    "kit_reference": None,
                    "original_unit_price": 0,
                    "product_id": 1440,
                    "product_rule_id": 1519574,
                    "quantity": 1,
                    "refundable": False,
                    "refunded_at": None,
                    "round_id": None,
                    "unit_price": 0,
                    "unit_quantity": 1
                }
            ]
        }
        payload['reservation']['rounds_attributes'].append(round_attribute)
    return payload


def login_headers(config):
    return {
        'User-Agent': config.user_agent,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': config.base_url,
    }


def reservation_headers(config, token):
    return {
        **login_headers(config),
        'X-CSRF-Token': token,
        'Referer': config.referer,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'DNT': '1',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
    }
