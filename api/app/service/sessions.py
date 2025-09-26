from datetime import datetime, timedelta
from app.store.models import Session, db
from app import utils


def store_session(user_id: int, session_data: dict, expires_hours: int = 24):
    expires_at = utils.ensure_utc_now() + timedelta(hours=expires_hours)

    session = Session.query.filter_by(user_id=user_id).first()
    if session:
        session.session_data = session_data
        session.expires_at = expires_at
        session.created_at = utils.ensure_utc_now()
    else:
        session = Session(
            user_id=user_id,
            session_data=session_data,
            expires_at=expires_at
        )
        db.session.add(session)

    db.session.commit()


def get_session(user_id: int):
    session = Session.query.filter_by(user_id=user_id).first()
    if not session or session.is_expired():
        if session:
            delete_session(user_id)
        return None
    return session.session_data


def delete_session(user_id: int):
    session = Session.query.filter_by(user_id=user_id).first()
    if session:
        db.session.delete(session)
        db.session.commit()


def cleanup_expired_sessions():
    expired_sessions = Session.query.filter(Session.expires_at < utils.ensure_utc_now()).all()
    for session in expired_sessions:
        db.session.delete(session)
    db.session.commit()
    return len(expired_sessions)