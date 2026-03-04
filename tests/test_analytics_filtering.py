import pytest

from habit_tracker.analytics import filter_by_periodicity, period_keys


# --- Filtering habits by periodicity -------------------------------------------------


def test_filter_by_periodicity_returns_daily_and_weekly_groups(habit_objects):
    """The predefined fixture should contain both daily and weekly habits."""
    daily_habits = filter_by_periodicity(habit_objects, "daily")
    weekly_habits = filter_by_periodicity(habit_objects, "weekly")

    # These counts come from predefined_data.HABITS (3 daily + 2 weekly).
    assert len(daily_habits) == 3
    assert len(weekly_habits) == 2


def test_filter_by_periodicity_ignores_case_and_extra_whitespace(habit_objects):
    """Users may type mixed case or include spaces/newlines; filtering should still work."""
    daily_1 = filter_by_periodicity(habit_objects, " DAILY ")
    daily_2 = filter_by_periodicity(habit_objects, "DaIlY")
    weekly = filter_by_periodicity(habit_objects, "\tWeEkLy\n")

    assert len(daily_1) == 3
    assert len(daily_2) == 3
    assert len(weekly) == 2


def test_filter_by_periodicity_returns_empty_for_unknown_values(habit_objects):
    """Unsupported periodicities should simply produce an empty list."""
    assert filter_by_periodicity(habit_objects, "monthly") == []
    assert filter_by_periodicity(habit_objects, "") == []
    assert filter_by_periodicity(habit_objects, None) == []


# --- Deriving period keys from completion timestamps --------------------------------


def test_period_keys_daily_are_unique_and_sorted():
    """Daily period keys should collapse multiple same-day completions into one key."""
    timestamps = [
        "2026-01-06T12:00:00",
        "2026-01-05T23:59:00",
        "2026-01-05T08:00:00",  # same day as 2026-01-05T23:59:00
    ]

    # Expect one key per day, sorted.
    assert period_keys(timestamps, "daily") == ["2026-01-05", "2026-01-06"]


def test_period_keys_weekly_are_unique_and_sorted():
    """Weekly keys should collapse timestamps that fall in the same ISO week."""
    timestamps = [
        "2026-01-12T12:00:00",  # 2026-W03
        "2026-01-06T12:00:00",  # 2026-W02
        "2026-01-05T08:00:00",  # same ISO week as 2026-01-06
    ]

    assert period_keys(timestamps, "weekly") == ["2026-W02", "2026-W03"]


def test_period_keys_rejects_invalid_periodicity_values():
    """Only 'daily' and 'weekly' are supported; anything else should raise."""
    with pytest.raises(ValueError):
        period_keys(["2026-01-05T12:00:00"], "monthly")

    with pytest.raises(ValueError):
        period_keys(["2026-01-05T12:00:00"], None)