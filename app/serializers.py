"""Shared response serialization for bookings."""

from .models import Booking
from .timeutils import iso_utc


def serialize_booking(booking: Booking) -> dict:
    if booking is None:
        raise ValueError("Booking cannot be None")

    return {
        "id": booking.id,
        "reference_code": booking.reference_code,
        "room_id": booking.room_id,
        "user_id": booking.user_id,
        "start_time": iso_utc(booking.start_time) if booking.start_time else None,
        "end_time": iso_utc(booking.end_time) if booking.end_time else None,
        "status": booking.status,
        "price_cents": booking.price_cents,
        "created_at": iso_utc(booking.created_at) if booking.created_at else None,
    }
