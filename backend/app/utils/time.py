"""Time handling.

SQLite does not reliably round-trip timezone-aware datetimes through
SQLAlchemy (they often come back naive on read), which caused
naive-vs-aware comparison errors throughout the allocation engine. To
avoid that entirely, every datetime in this backend — in memory and in
the database — is a NAIVE datetime representing IST wall-clock time.
Only `iso()`, used when serializing to JSON for the frontend, attaches
the `+05:30` offset explicitly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def now() -> datetime:
    """Current IST wall-clock time, as a naive datetime (see module docstring)."""
    utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
    return utc_now + timedelta(hours=5, minutes=30)


def iso(dt: datetime) -> str:
    """Format a naive IST datetime as an ISO 8601 string with the +05:30
    offset, which is what the frontend's `new Date(iso)` expects."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"


def minutes_from_now(minutes: float, base: datetime | None = None) -> datetime:
    return (base if base is not None else now()) + timedelta(minutes=minutes)
