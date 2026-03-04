import pytest

from habit_tracker.analytics import current_streak_for, longest_streak_all, longest_streak_for
from habit_tracker.predefined_data import (
    FOUR_WEEKS_DAYS,
    FOUR_WEEKS_START,
    EXPECTED_CURRENT_STREAKS_ENDING_AT_LATEST,
    EXPECTED_LONGEST_STREAKS,
    completions_by_habit_name,
)


def test_predefined_fixture_covers_exactly_four_weeks_for_daily_perfect():
    """Sanity check the fixture window using the simplest habit: Daily Perfect."""
    fixture = completions_by_habit_name()

    # "Daily Perfect" should have one completion per day for 4 weeks -> 28 completions.
    assert len(fixture["Daily Perfect"]) == FOUR_WEEKS_DAYS

    # First completion should be on the configured start date at noon.
    first_ts = fixture["Daily Perfect"][0]
    assert first_ts.startswith(FOUR_WEEKS_START.isoformat())
    assert first_ts.endswith("T12:00:00")


def test_streak_calculations_match_expected_values_for_fixture(predefined_completions):
    """Verify streak outputs against the deterministic expected tables.

    This is the most rubric-aligned test in the suite:
    it proves that your streak logic matches the known-good 4-week dataset.
    """
    for habit_name, timestamps in predefined_completions.items():
        # The fixture naming convention encodes periodicity (Weekly* vs Daily*).
        periodicity = "weekly" if habit_name.startswith("Weekly") else "daily"

        assert longest_streak_for(timestamps, periodicity) == EXPECTED_LONGEST_STREAKS[habit_name]
        assert current_streak_for(timestamps, periodicity) == EXPECTED_CURRENT_STREAKS_ENDING_AT_LATEST[habit_name]


def test_longest_streak_all_picks_the_expected_best_habit(habit_objects, predefined_completions):
    """Longest streak across all habits should be 'Daily Perfect' with 28 periods.

    In conftest we intentionally set habit.id == habit.name for analytics-only tests.
    That makes it easy to retrieve the correct completion list by ID.
    """
    best_habit, best_streak = longest_streak_all(
        habit_objects,
        lambda habit_id: predefined_completions[habit_id],
    )

    assert best_habit is not None
    assert best_habit.name == "Daily Perfect"
    assert best_streak == 28


def test_seeded_tracker_overview_matches_expected_tables(seeded_tracker):
    """Integration test: verify the DB-backed overview matches expected streak tables.

    This runs through the full stack:
    SQLiteStorage -> HabitTracker -> analytics functions.
    """
    overview = seeded_tracker.analyze_overview()

    # analyze_overview returns: (Habit, current_streak, longest_streak)
    overview_by_name = {habit.name: (current, longest) for (habit, current, longest) in overview}

    # All predefined habits should appear in the overview output.
    assert set(overview_by_name.keys()) == set(EXPECTED_LONGEST_STREAKS.keys())

    # Verify exact streak values for each habit.
    for habit_name in EXPECTED_LONGEST_STREAKS:
        current, longest = overview_by_name[habit_name]
        assert longest == EXPECTED_LONGEST_STREAKS[habit_name]
        assert current == EXPECTED_CURRENT_STREAKS_ENDING_AT_LATEST[habit_name]