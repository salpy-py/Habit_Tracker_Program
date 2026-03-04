# tests/conftest.py
"""
Shared pytest fixtures for the habit tracker project.

Pytest automatically discovers fixtures defined here and makes them available
to all test files in this folder.
"""

import pytest

from habit_tracker.models import Habit
from habit_tracker.predefined_data import HABITS, completions_by_habit_name
from habit_tracker.storage import SQLiteStorage
from habit_tracker.tracker import HabitTracker


@pytest.fixture()
def db_path(tmp_path) -> str:
    """Temporary SQLite DB path (unique per test)."""
    return str(tmp_path / "habits_test.db")


@pytest.fixture()
def storage(db_path) -> SQLiteStorage:
    """Fresh SQLiteStorage per test (isolated DB)."""
    return SQLiteStorage(db_path)


@pytest.fixture()
def tracker(storage) -> HabitTracker:
    """Fresh HabitTracker per test (isolated DB)."""
    return HabitTracker(storage)


@pytest.fixture()
def predefined_habits():
    """The 4-week predefined habits metadata (name + periodicity)."""
    return HABITS


@pytest.fixture()
def predefined_completions():
    """The 4-week predefined completion timestamps per habit name."""
    return completions_by_habit_name()


@pytest.fixture()
def habit_objects(predefined_habits):
    """
    Habit objects for analytics tests.

    Uses habit name as id so tests can stay simple and deterministic.
    """
    return [
        Habit(
            id=h.name,
            name=h.name,
            periodicity=h.periodicity,
            created_at="2026-01-01T00:00:00",
        )
        for h in predefined_habits
    ]


@pytest.fixture()
def seeded_tracker(tracker, predefined_habits, predefined_completions) -> HabitTracker:
    """
    Tracker seeded with the 4-week predefined habits and their time-series completions.

    Useful for end-to-end analytics tests that go through real storage.
    """
    # Create habits
    for h in predefined_habits:
        tracker.add_habit(h.name, h.periodicity)

    # Add completions
    for habit_name, timestamps in predefined_completions.items():
        for ts in timestamps:
            tracker.check_off(habit_name, timestamp_iso=ts)

    return tracker