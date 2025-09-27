from flask import Blueprint
from flask import current_app as app
from flask import jsonify

from .auth import auth_bp
from .bookings import bookings_bp
from .notifications import notifications_bp
from .users import users_bp

api_bp = Blueprint("api", __name__)

api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(users_bp)
api_bp.register_blueprint(bookings_bp)
api_bp.register_blueprint(notifications_bp)


@api_bp.errorhandler(404)
def handle_404(error):
    app.logger.error(f"Not found: {str(error)}")
    return jsonify({"error": "Not found"}), 404


@api_bp.errorhandler(500)
def handle_500(error):
    app.logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({"error": "Something went wrong. Please try again."}), 500
