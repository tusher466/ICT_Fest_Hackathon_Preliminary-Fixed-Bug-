import time
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from .. import cache
from ..auth import get_current_user
from ..database import get_db
from ..errors import AppError
from ..models import Booking, Room, User
from ..schemas import BookingCreateRequest
from ..serializers import serialize_booking
from ..services import notifications, ratelimit, reference, stats
from ..services.refunds import log_refund
from ..timeutils import iso_utc, parse_input_datetime

router = APIRouter(tags=["bookings"])

MIN_DURATION_HOURS = 1
MAX_DURATION_HOURS = 8
QUOTA_LIMIT = 3
QUOTA_WINDOW_HOURS = 24


def _has_conflict(db: Session, room_id: int, start: datetime, end: datetime) -> bool:
    # BUG FIXED: Query overlapping ranges inside the database instead of doing a loop in Python
    conflict = (
        db.query(Booking)
        .filter(
            Booking.room_id == room_id,
            Booking.status == "confirmed",
            Booking.start_time < end,
            Booking.end_time > start,
        )
        .first()
    )
    return conflict is not None


def _check_quota(db: Session, user_id: int, now: datetime, start: datetime) -> None:
    window_end = now + timedelta(hours=QUOTA_WINDOW_HOURS)
    if not (now < start <= window_end):
        return
    count = (
        db.query(Booking)
        .filter(
            Booking.user_id == user_id,
            Booking.status == "confirmed",
            Booking.start_time > now,
            Booking.start_time <= window_end,
        )
        .count()
    )
    if count >= QUOTA_LIMIT:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            error_code="QUOTA_EXCEEDED",
            message="Booking quota exceeded",
        )


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ratelimit.record_and_check(user.id)

    start = parse_input_datetime(payload.start_time)
    end = parse_input_datetime(payload.end_time)
    now = datetime.utcnow()

    # BUG FIXED: Prevent logical anomalies where end_time is before or equal to start_time
    if start >= end:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_BOOKING_WINDOW",
            message="start_time must be before end_time",
        )

    if start <= now - timedelta(seconds=300):
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_BOOKING_WINDOW",
            message="start_time must be in the future",
        )

    duration_hours = (end - start).total_seconds() / 3600
    if duration_hours != int(duration_hours):
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_BOOKING_WINDOW",
            message="duration must be a whole number of hours",
        )
    duration_hours = int(duration_hours)
    
    # BUG FIXED: Checked both MIN and MAX duration ranges
    if duration_hours < MIN_DURATION_HOURS or duration_hours > MAX_DURATION_HOURS:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_BOOKING_WINDOW",
            message=f"Duration must be between {MIN_DURATION_HOURS} and {MAX_DURATION_HOURS} hours",
        )

    room = db.query(Room).filter(Room.id == payload.room_id, Room.org_id == user.org_id).first()
    if room is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ROOM_NOT_FOUND",
