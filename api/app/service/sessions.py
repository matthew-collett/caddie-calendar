import uuid
from datetime import timedelta

from app import utils
from app.store.models import Session, db


def store_session(user_id: int, session_data: dict, expires_hours: int = 24):
    expires_at = utils.ensure_utc_now() + timedelta(hours=expires_hours)
    session_id = str(uuid.uuid4())

    session = Session(
        session_id=session_id,
        user_id=user_id,
        session_data=session_data,
        expires_at=expires_at,
    )
    db.session.add(session)
    db.session.commit()

    return session_id


def get_session(session_id: str):
    session = Session.query.filter_by(session_id=session_id).first()
    if not session or session.is_expired():
        if session:
            delete_session(session_id)
        return None
    return session.session_data


def delete_session(session_id: str):
    session = Session.query.filter_by(session_id=session_id).first()
    if session:
        db.session.delete(session)
        db.session.commit()


def get_user_sessions(user_id: int):
    sessions = Session.query.filter_by(user_id=user_id).all()
    return [session.session_data for session in sessions if not session.is_expired()]


def cleanup_expired_sessions():
    expired_sessions = Session.query.filter(
        Session.expires_at < utils.ensure_utc_now()
    ).all()
    for session in expired_sessions:
        db.session.delete(session)
    db.session.commit()
    return len(expired_sessions)
