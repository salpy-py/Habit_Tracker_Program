import pytest

from habit_tracker.analytics import (
    current_streak_for,
    filter_by_periodicity,
    longest_streak_all,
    longest_streak_for,
    period_keys,
)
from habit_tracker.predefined_data import (
    EXPECTED_CURRENT_STREAKS_ENDING_AT_LATEST,
    EXPECTED_LONGEST_STREAKS,
)


def test_filter_by_periodicity_splits_daily_and_weekly_habits(habit_objects):
    """Filtering should return the correct habits for each periodicity."""
    daily_habits = filter_by_periodicity(habit_objects, "DAILY")
    weekly_habits = filter_by_periodicity(habit_objects, "weekly")

    # Exact expected habit names (comes from predefined_data.HABITS).
    assert {h.name for h in daily_habits} == {"Daily Perfect", "Daily Skip Sundays", "Daily One Gap"}
    assert {h.name for h in weekly_habits} == {"Weekly Perfect", "Weekly Miss Week 2"}


def test_streaks_match_expected_tables_for_each_predefined_habit(habit_objects, predefined_completions):
    """The fixture dataset is deterministic, so streak outputs must match the expected tables."""
    for habit in habit_objects:
        timestamps = predefined_completions[habit.name]

        # These are the key rubric checks: longest + current streak must match expected values.
        assert longest_streak_for(timestamps, habit.periodicity) == EXPECTED_LONGEST_STREAKS[habit.name]
        assert current_streak_for(timestamps, habit.periodicity) == EXPECTED_CURRENT_STREAKS_ENDING_AT_LATEST[habit.name]


def test_longest_streak_all_selects_daily_perfect(habit_objects, predefined_completions):
    """Across the whole predefined dataset, Daily Perfect should win with a streak of 28."""
    # longest_streak_all calls get_completions_fn(habit.id).
    # In conftest, we intentionally set habit.id == habit.name to make lookups trivial.
    best_habit, best_streak = longest_streak_all(
        habit_objects,
        lambda habit_id: predefined_completions.get(habit_id, []),
    )

    assert best_habit is not None
    assert best_habit.name == "Daily Perfect"
    assert best_streak == 28


def test_period_keys_collapses_duplicates_within_the_same_period():
    """Multiple check-offs inside one period should count once (daily and weekly)."""
    # Daily duplicates should collapse into a single date key.
    daily_timestamps = ["2026-01-05T12:00:00", "2026-01-05T13:30:00"]
    assert period_keys(daily_timestamps, "daily") == ["2026-01-05"]

    # Weekly duplicates inside one ISO week should collapse into one week key.
    weekly_timestamps = ["2026-01-05T12:00:00", "2026-01-07T12:00:00"]
    assert len(period_keys(weekly_timestamps, "weekly")) == 1


def test_period_keys_rejects_unsupported_periodicity_values():
    """Only daily/weekly are supported in this project; anything else should raise."""
    with pytest.raises(ValueError):
        period_keys(["2026-01-05T12:00:00"], "monthly")