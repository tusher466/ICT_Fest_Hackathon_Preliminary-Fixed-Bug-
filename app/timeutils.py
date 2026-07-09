"""Helpers for parsing input datetimes and rendering UTC responses."""

from datetime import datetime, timezone


def parse_input_datetime(value: str) -> datetime:
    """
    Parse an ISO 8601 datetime into a naive UTC datetime for storage.

    Offset-aware datetimes are converted to UTC before removing the timezone.
    Naive datetimes are treated as already being UTC.
    """
    dt = datetime.fromisoformat(value)

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

    return dt


def iso_utc(dt: datetime) -> str:
    """
    Render a stored naive UTC datetime with an explicit UTC designator.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")
