from datetime import datetime, timezone, timedelta, date
from typing import Tuple

def now_utc_iso() -> str:
    """Current time in UTC ISO-8601 (seconds precision)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def parse_iso(dt_iso: str) -> datetime:
    """Parse ISO string. Python 3.7+ supports timezone offsets via fromisoformat."""
    return datetime.fromisoformat(dt_iso)

def to_local_date(dt: datetime) -> date:
    """
    Convert aware datetime to system local date.
    This ensures 'late-night' completions fall into the correct local day.
    """
    if dt.tzinfo is None:
        return dt.date()   # treat naive as local
    return dt.astimezone().date()

def day_key(dt_iso: str) -> str:
    d = to_local_date(parse_iso(dt_iso))
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"

def iso_week_key(dt_iso: str) -> str:
    d = to_local_date(parse_iso(dt_iso))
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year:04d}-W{iso_week:02d}"

def parse_iso_week_key(key: str) -> Tuple[int, int]:
    year_s, week_s = key.split("-W")
    return int(year_s), int(week_s)

def iso_week_monday(iso_year: int, iso_week: int) -> date:
    """
    Monday date of an ISO week (Python 3.7 compatible).
    ISO week 1 is the week containing Jan 4th.
    """
    jan4 = date(iso_year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())  # Monday=0
    return week1_monday + timedelta(weeks=iso_week - 1)

def local_tzinfo():
    return datetime.now().astimezone().tzinfo

def local_datetime_to_utc_iso(d: date, hour: int, minute: int) -> str:
    """Build a local datetime and store it as UTC ISO string."""
    tz = local_tzinfo()
    dt_local = datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)
    dt_utc = dt_local.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.isoformat()
