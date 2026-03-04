import pytest

from habit_tracker.analytics import current_streak_for, longest_streak_for
from habit_tracker.time_utils import day_key, iso_week_key


def test_streaks_are_zero_when_there_are_no_completions():
    """No completions should always mean no streak (regardless of periodicity)."""
    assert longest_streak_for([], "daily") == 0
    assert current_streak_for([], "daily") == 0
    assert longest_streak_for([], "weekly") == 0
    assert current_streak_for([], "weekly") == 0


def test_multiple_checkoffs_in_the_same_day_do_not_inflate_daily_streak():
    """Three check-offs on the same date still count as one successful day."""
    timestamps = [
        "2026-01-05T08:00:00",
        "2026-01-05T12:00:00",
        "2026-01-05T23:59:00",
    ]

    # All timestamps belong to the same daily period => streak should be 1.
    assert longest_streak_for(timestamps, "daily") == 1
    assert current_streak_for(timestamps, "daily") == 1


def test_multiple_checkoffs_in_the_same_week_do_not_inflate_weekly_streak():
    """Several check-offs within one ISO week still count as one successful week."""
    timestamps = [
        "2026-01-05T08:00:00",  # ISO week start
        "2026-01-06T12:00:00",
        "2026-01-07T23:59:00",
    ]

    assert longest_streak_for(timestamps, "weekly") == 1
    assert current_streak_for(timestamps, "weekly") == 1


def test_streak_calculation_is_order_independent_for_daily_habits():
    """Completion timestamps may be stored/retrieved out of order; streak logic should still work."""
    timestamps = [
        "2026-01-07T12:00:00",
        "2026-01-05T12:00:00",
        "2026-01-06T12:00:00",
    ]

    # Days 5, 6, 7 are consecutive => 3-day streak.
    assert longest_streak_for(timestamps, "daily") == 3
    assert current_streak_for(timestamps, "daily") == 3


def test_missing_a_day_breaks_a_daily_streak():
    """If a day is missed in between, the chain should break."""
    timestamps = [
        "2026-01-05T12:00:00",
        "2026-01-06T12:00:00",
        # No completion on 2026-01-07
        "2026-01-08T12:00:00",
    ]

    # Longest run is 2 (5th->6th). Latest completion (8th) starts a new streak of 1.
    assert longest_streak_for(timestamps, "daily") == 2
    assert current_streak_for(timestamps, "daily") == 1


def test_missing_a_week_breaks_a_weekly_streak():
    """Weekly streaks should break when a whole ISO week is skipped."""
    timestamps = [
        "2026-01-05T12:00:00",  # week A
        "2026-01-12T12:00:00",  # week A+1
        # Missing week A+2
        "2026-01-26T12:00:00",  # week A+3
    ]

    assert longest_streak_for(timestamps, "weekly") == 2
    assert current_streak_for(timestamps, "weekly") == 1


def test_period_key_helpers_collapse_multiple_events_into_one_period():
    """Sanity check: time_utils collapses events into the same day/week bucket."""
    # Same day => same day_key
    assert day_key("2026-01-05T08:00:00") == day_key("2026-01-05T23:59:00")

    # Same ISO week => same iso_week_key
    assert iso_week_key("2026-01-05T08:00:00") == iso_week_key("2026-01-06T23:59:00")


def test_invalid_periodicity_values_raise_value_error():
    """Analytics functions should reject unsupported periodicities."""
    with pytest.raises(ValueError):
        longest_streak_for(["2026-01-05T12:00:00"], "monthly")

    with pytest.raises(ValueError):
        current_streak_for(["2026-01-05T12:00:00"], "yearly")