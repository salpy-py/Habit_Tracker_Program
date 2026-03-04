"""Predefined 4-week time-series data.

This module provides deterministic habit completion timestamps that are used by unit tests
to verify streak calculations. Times are stored as ISO strings without a timezone offset to
avoid dependence on a machine's local timezone.

The data spans exactly 4 weeks (28 days) starting on a Monday.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List


FOUR_WEEKS_START: date = date(2026, 1, 5)  # Monday
FOUR_WEEKS_DAYS: int = 28


def _noon_iso(d: date) -> str:
    """Return a stable ISO timestamp for a given date."""
    return f"{d.isoformat()}T12:00:00"


@dataclass(frozen=True)
class PredefinedHabit:
    name: str
    periodicity: str  # 'daily' or 'weekly'


HABITS: List[PredefinedHabit] = [
    PredefinedHabit("Daily Perfect", "daily"),
    PredefinedHabit("Daily Skip Sundays", "daily"),
    PredefinedHabit("Daily One Gap", "daily"),
    PredefinedHabit("Weekly Perfect", "weekly"),
    PredefinedHabit("Weekly Miss Week 2", "weekly"),
]


def completions_by_habit_name() -> Dict[str, List[str]]:
    """Return {habit_name: [timestamp_iso, ...]} for the 4-week window."""
    start = FOUR_WEEKS_START

    # Helper list of 28 dates
    days = [start + timedelta(days=i) for i in range(FOUR_WEEKS_DAYS)]

    data: Dict[str, List[str]] = {}

    # 1) Daily Perfect: every single day
    data["Daily Perfect"] = [_noon_iso(d) for d in days]

    # 2) Daily Skip Sundays: complete Mon-Sat, skip Sundays (weekday() == 6)
    data["Daily Skip Sundays"] = [_noon_iso(d) for d in days if d.weekday() != 6]

    # 3) Daily One Gap: 10 days done, 1 day missed, then 17 days done
    #    (Total = 27 completions, longest streak = 17)
    first_block = days[:10]
    second_block = days[11:]  # skip index 10
    data["Daily One Gap"] = [_noon_iso(d) for d in (first_block + second_block)]

    # Weekly completions are recorded on Mondays.
    mondays = [start + timedelta(days=7 * w) for w in range(4)]

    # 4) Weekly Perfect: every week
    data["Weekly Perfect"] = [_noon_iso(d) for d in mondays]

    # 5) Weekly Miss Week 2: miss the second Monday
    data["Weekly Miss Week 2"] = [_noon_iso(mondays[0]), _noon_iso(mondays[2]), _noon_iso(mondays[3])]

    return data


# Expected values used by unit tests.
EXPECTED_LONGEST_STREAKS = {
    "Daily Perfect": 28,
    "Daily Skip Sundays": 6,
    "Daily One Gap": 17,
    "Weekly Perfect": 4,
    "Weekly Miss Week 2": 2,
}

EXPECTED_CURRENT_STREAKS_ENDING_AT_LATEST = {
    # Current streak is computed ending at the latest recorded completion period.
    "Daily Perfect": 28,
    "Daily Skip Sundays": 6,
    "Daily One Gap": 17,
    "Weekly Perfect": 4,
    "Weekly Miss Week 2": 2,
}
