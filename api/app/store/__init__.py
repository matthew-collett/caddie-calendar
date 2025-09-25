from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

add = db.session.add
commit = db.session.commit
rollback = db.session.rollback
delete = db.session.delete


def init_app(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()


__all__ = ["add", "commit", "rollback", "delete"]
