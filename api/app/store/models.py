import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from enum import Enum
from typing import List, Optional

from app import utils
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType

from . import db


@dataclass
class Player:
    user_id: int
    affiliation_id: int
    first_name: str
    last_name: str
    handicap: Optional[int] = None
    note: Optional[str] = None


class Status(Enum):
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class NotificationType(Enum):
    BOOKING_SUCCESS = "BOOKING_SUCCESS"
    BOOKING_FAILED = "BOOKING_FAILED"


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    affiliation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="America/Halifax")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utils.ensure_utc_now)
    bookings = relationship("Booking", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    sessions = relationship("Session", back_populates="user")

    def to_dict(self):
        return {"id": self.id, "full_name": self.full_name, "email": self.email, "timezone": self.timezone}


class Booking(db.Model):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_time: Mapped[time] = mapped_column(Time, nullable=False)
    holes: Mapped[int] = mapped_column(Integer, nullable=False)
    players: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Status] = mapped_column(
        ChoiceType(Status, impl=String()), nullable=False, default=Status.PENDING
    )
    booking_id: Mapped[str] = mapped_column(String(100), nullable=True)
    actual_time: Mapped[time] = mapped_column(Time, nullable=True)
    error_details: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utils.ensure_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utils.ensure_utc_now)
    user = relationship("User", back_populates="bookings")

    def get_players(self) -> List[Player]:
        players_data = json.loads(self.players) if self.players else []
        return [Player(**player) for player in players_data]

    def set_players(self, players: List[Player]) -> None:
        self.players = json.dumps([asdict(player) for player in players])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "booking_date": utils.serialize_date(self.booking_date),
            "target_time": utils.serialize_time(self.target_time),
            "holes": self.holes,
            "players": json.loads(self.players) if self.players else [],
            "status": self.status.value,
            "booking_id": self.booking_id,
            "actual_time": utils.serialize_time(self.actual_time),
            "error_details": self.error_details,
            "created_at": utils.serialize_datetime(self.created_at),
            "updated_at": utils.serialize_datetime(self.updated_at),
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    booking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        ChoiceType(NotificationType, impl=String()), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utils.ensure_utc_now)
    user = relationship("User", back_populates="notifications")
    booking = relationship("Booking")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "booking_id": self.booking_id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": utils.serialize_datetime(self.created_at),
        }


class Session(db.Model):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    session_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utils.ensure_utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def is_expired(self):
        return utils.ensure_utc_now() > self.expires_at
