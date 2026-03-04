"""Analytics helpers for the Habit Tracker.

This module provides the analytics your CLI relies on, including:
- listing habits (all habits or filtered by periodicity)
- computing streaks for a habit (current and longest)
- identifying the habit with the longest streak overall

Key detail about streaks:
Streaks are measured in completed *periods*, not in raw check-off counts.
- Daily habits: one period equals one calendar day (YYYY-MM-DD)
- Weekly habits: one period equals one ISO week (YYYY-W##)

If a user checks off a habit multiple times within the same period,
it still counts as just ONE successful period.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Callable, List, Optional, Tuple

from .models import Habit
from .time_utils import day_key, iso_week_key, parse_iso_week_key, iso_week_monday


def _normalize_periodicity(periodicity: str) -> str:
    """Normalize periodicity input to a clean lowercase value."""
    return (periodicity or "").strip().lower()


def filter_by_periodicity(habits: List[Habit], periodicity: str) -> List[Habit]:
    """Return habits that match the requested periodicity (case-insensitive).

    Example:
        filter_by_periodicity(habits, " DAILY ") -> returns all daily habits
    """
    wanted = _normalize_periodicity(periodicity)
    return [habit for habit in habits if habit.periodicity == wanted]


def period_keys(completions_iso: List[str], periodicity: str) -> List[str]:
    """Return sorted, unique "period keys" derived from completion timestamps.

    A "period key" is the unit we use to count streaks:
      - daily  -> "YYYY-MM-DD"
      - weekly -> "YYYY-W##" (ISO week key)

    Multiple completions within the same period collapse into one key.
    """
    normalized = _normalize_periodicity(periodicity)
    if normalized not in ("daily", "weekly"):
        raise ValueError("periodicity must be 'daily' or 'weekly'")

    if normalized == "daily":
        keys = [day_key(ts) for ts in completions_iso]
    else:
        keys = [iso_week_key(ts) for ts in completions_iso]

    # Using a set removes duplicates (multiple check-offs in same period),
    # then we sort to make downstream logic predictable and test-friendly.
    return sorted(set(keys))


def _longest_consecutive_run(dates: List[date], step_days: int) -> int:
    """Return the length of the longest run of evenly spaced consecutive dates.

    For daily streaks: step_days=1
    For weekly streaks: step_days=7 (we represent weeks by their Monday date)

    We remove duplications and sort dates so the function is resilient to:
    - duplicate completions
    - unsorted inputs
    """
    if not dates:
        return 0

    unique_sorted = sorted(set(dates))
    expected_step = timedelta(days=step_days)

    best_run = 1
    current_run = 1

    for idx in range(1, len(unique_sorted)):
        if unique_sorted[idx] - unique_sorted[idx - 1] == expected_step:
            current_run += 1
        else:
            best_run = max(best_run, current_run)
            current_run = 1

    return max(best_run, current_run)


def longest_streak_for(completions_iso: List[str], periodicity: str) -> int:
    """Compute the longest streak (in periods) for a habit's completion timestamps."""
    normalized = _normalize_periodicity(periodicity)
    keys = period_keys(completions_iso, normalized)
    if not keys:
        return 0

    if normalized == "daily":
        # Keys are already "YYYY-MM-DD", so we can convert straight to date objects.
        completed_days = [date.fromisoformat(k) for k in keys]
        return _longest_consecutive_run(completed_days, step_days=1)

    # Weekly: convert each ISO week key (YYYY-W##) to the Monday of that week.
    completed_week_mondays = [iso_week_monday(*parse_iso_week_key(k)) for k in keys]
    return _longest_consecutive_run(completed_week_mondays, step_days=7)


def current_streak_for(completions_iso: List[str], periodicity: str) -> int:
    """Compute the current streak ending at the most recently completed period.

    Note on the definition used here:
    "Current streak" means the streak that ends at the latest *completed* period,
    not necessarily "as of today/this week".

    This keeps the function deterministic and easy to unit test without needing
    to look at the current system time.
    """
    normalized = _normalize_periodicity(periodicity)
    keys = period_keys(completions_iso, normalized)
    if not keys:
        return 0

    if normalized == "daily":
        completed_days = sorted(set(date.fromisoformat(k) for k in keys))

        # Walk backwards from the most recent day and count how long the chain continues.
        streak = 1
        for idx in range(len(completed_days) - 1, 0, -1):
            if completed_days[idx] - completed_days[idx - 1] == timedelta(days=1):
                streak += 1
            else:
                break
        return streak

    # Weekly: represent weeks by their Monday date and then apply the same logic.
    completed_week_mondays = sorted(
        set(iso_week_monday(*parse_iso_week_key(k)) for k in keys)
    )

    streak = 1
    for idx in range(len(completed_week_mondays) - 1, 0, -1):
        if completed_week_mondays[idx] - completed_week_mondays[idx - 1] == timedelta(
            days=7
        ):
            streak += 1
        else:
            break
    return streak


def longest_streak_all(
    habits: List[Habit],
    get_completions_fn: Callable[[str], List[str]],
) -> Tuple[Optional[Habit], int]:
    """Find the habit with the longest streak across all habits.

    Returns:
        (best_habit, best_streak)

    If there are no habits, best_habit will be None and best_streak will be 0.
    """
    best_habit: Optional[Habit] = None
    best_streak = 0

    for habit in habits:
        completions = get_completions_fn(habit.id)
        streak = longest_streak_for(completions, habit.periodicity)

        if streak > best_streak:
            best_habit = habit
            best_streak = streak

    return best_habit, best_streak
