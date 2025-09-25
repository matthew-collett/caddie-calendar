from flask import Blueprint
from .auth import auth_bp
from .users import users_bp
from .bookings import bookings_bp
from .notifications import notifications_bp


api_bp = Blueprint("api", __name__)

api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(users_bp)
api_bp.register_blueprint(bookings_bp)
api_bp.register_blueprint(notifications_bp)
