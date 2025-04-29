import os
from dataclasses import dataclass
from datetime import date, time
from model import Member, Members
from services import secrets_manager


@dataclass
class Config:
    target_time: time
    booker: Member
    players: list[Member]
    holes: int
    date: date
    email: str
    password: str
    token: str = None
    club_id: str = os.getenv("CLUB_ID")
    club_name: str = os.getenv("CLUB_NAME")
    course_id: str = os.getenv("COURSE_ID")
    currency_code: str = os.getenv("CURRENCY_CODE")
    fernet_key: bytes
    user_agent: str = os.getenv("USER_AGENT")
    referer: str = os.getenv("REFERER")
    base_url: str = os.getenv("BASE_URL")
    region: str = os.getenv("AWS_REGION")
    sender_email: str = os.getenv("SENDER_EMAIL")


def create_config_for_day(user, day_of_week, booking_date):
    matching_bookings = [b for b in user.get('weeklyBookings', [])
                         if b['dayOfWeek'] == day_of_week]

    if not matching_bookings:
        return None

    booking = matching_bookings[0]

    time_parts = booking['targetTime'].split(':')
    target_time = time(int(time_parts[0]), int(time_parts[1]))

    players = [getattr(Members, player_id) for player_id in booking['players']]
    booker = getattr(Members, booking['booker'])

    fernet_key = secrets_manager.get_secret('caddie-calendar-fernet-key')
    return Config(
        target_time=target_time,
        booker=booker,
        players=players,
        holes=booking['holes'],
        fernet_key=fernet_key,
        date=booking_date,
        email=user['email'],
        password=user['password']
    )
