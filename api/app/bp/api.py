from app.logger import logger
from flask import Blueprint, jsonify

from .auth import auth_bp
from .bookings import bookings_bp
from .notifications import notifications_bp
from .users import users_bp

api_bp = Blueprint("api", __name__)

api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(users_bp)
api_bp.register_blueprint(bookings_bp)
api_bp.register_blueprint(notifications_bp)


@api_bp.errorhandler(500)
def handle_500(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({"error": "Something went wrong. Please try again."}), 500
