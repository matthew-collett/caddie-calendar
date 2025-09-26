from app import service as svc
from app.middlewares import require_auth
from flask import Blueprint, jsonify, request

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


@bookings_bp.route("", methods=["POST"])
@require_auth
def create_booking_endpoint():
    data = request.get_json()

    if not data or not all(
        key in data for key in ["booking_date", "target_time", "holes", "players"]
    ):
        return (
            jsonify(
                {"error": "booking_date, target_time, holes, and players required"}
            ),
            400,
        )

    booking = svc.bookings.create_booking(request.user_id, data)
    return jsonify({"id": booking.id}), 201


@bookings_bp.route("", methods=["GET"])
@require_auth
def list_bookings():
    bookings = [
        {**booking.to_dict(), "role": "host"}
        for booking in svc.bookings.get_user_bookings(request.user_id)
    ]
    bookings.extend(
        [
            {**booking.to_dict(), "role": "guest"}
            for booking in svc.bookings.get_particpating_bookings(request.user_id)
        ]
    )
    return jsonify(bookings), 200


@bookings_bp.route("/<int:booking_id>", methods=["DELETE"])
@require_auth
def delete_booking(booking_id):
    success = svc.bookings.delete_booking(booking_id, request.user_id)
    if not success:
        return jsonify({"error": "Booking not found"}), 404

    return jsonify({"message": "Booking deleted successfully"}), 200
