import pytest


def test_add_habit_creates_and_persists(tracker):
    """Adding a habit should return a Habit object and store it in the database."""
    created = tracker.add_habit("Test Habit", "daily")
    assert created.name == "Test Habit"
    assert created.periodicity == "daily"

    # Make sure it actually persisted (not just returned from memory).
    saved = tracker.get_habits()
    assert len(saved) == 1
    assert saved[0].name == "Test Habit"
    assert saved[0].periodicity == "daily"


def test_add_habit_rejects_duplicate_names(tracker):
    """Habit names are unique; adding the same name twice should fail."""
    tracker.add_habit("Test Habit", "daily")

    with pytest.raises(ValueError):
        tracker.add_habit("Test Habit", "daily")


@pytest.mark.parametrize("invalid_name", ["", "   ", None])
def test_add_habit_rejects_blank_or_missing_name(tracker, invalid_name):
    """Name is required and cannot be blank/whitespace."""
    with pytest.raises(ValueError):
        tracker.add_habit(invalid_name, "daily")


@pytest.mark.parametrize("invalid_period", ["", "monthly", "YEARLY", "abc", None])
def test_add_habit_rejects_invalid_periodicity(tracker, invalid_period):
    """Only 'daily' and 'weekly' are valid periodicities in this project."""
    with pytest.raises(ValueError):
        tracker.add_habit("Some Habit", invalid_period)


def test_edit_habit_allows_renaming_by_name(tracker):
    """A habit can be located by name and renamed."""
    original = tracker.add_habit("Test Habit", "daily")

    updated = tracker.edit_habit("Test Habit", new_name="Renamed Habit")
    assert updated.id == original.id
    assert updated.name == "Renamed Habit"
    assert updated.periodicity == "daily"  # unchanged

    # Confirm the rename is persisted.
    names = [h.name for h in tracker.get_habits()]
    assert names == ["Renamed Habit"]


def test_edit_habit_allows_changing_periodicity_by_id(tracker):
    """A habit can be located by ID and updated."""
    habit = tracker.add_habit("Test Habit", "daily")

    updated = tracker.edit_habit(habit.id, new_periodicity="weekly")
    assert updated.id == habit.id
    assert updated.periodicity == "weekly"


def test_edit_habit_rejects_renaming_to_existing_name(tracker):
    """Renaming a habit to an existing name should be rejected."""
    tracker.add_habit("A", "daily")
    tracker.add_habit("B", "daily")

    with pytest.raises(ValueError):
        tracker.edit_habit("A", new_name="B")


def test_edit_habit_requires_at_least_one_change(tracker):
    """Calling edit with no new_name and no new_periodicity should raise."""
    tracker.add_habit("A", "daily")

    with pytest.raises(ValueError):
        tracker.edit_habit("A")  # no changes provided


def test_checkoff_creates_a_completion_record(tracker):
    """A check-off should insert a timestamp into the habit's completion history."""
    habit = tracker.add_habit("Test Habit", "daily")

    tracker.check_off("Test Habit", timestamp_iso="2026-01-05T12:00:00")
    completions = tracker.get_completions(habit.id)

    assert completions == ["2026-01-05T12:00:00"]


def test_checkoff_unknown_habit_raises(tracker):
    """Check-offs require a valid habit key (name or ID)."""
    with pytest.raises(ValueError):
        tracker.check_off("Does Not Exist", timestamp_iso="2026-01-05T12:00:00")


def test_delete_habit_removes_the_habit(tracker):
    """Deleting an existing habit should return True and remove it from storage."""
    tracker.add_habit("Test Habit", "daily")

    assert tracker.delete_habit("Test Habit") is True
    assert tracker.get_habits() == []


def test_delete_unknown_habit_returns_false(tracker):
    """Deleting a missing habit should be a safe no-op and return False."""
    assert tracker.delete_habit("Unknown") is False


def test_duplicate_completion_timestamp_is_ignored(tracker):
    """Duplicate completion timestamps should not be stored twice.

    SQLiteStorage uses INSERT OR IGNORE plus a unique index on (habit_id, completed_at),
    so inserting an identical completion event should effectively do nothing.
    """
    habit = tracker.add_habit("Test Habit", "daily")

    tracker.check_off("Test Habit", timestamp_iso="2026-01-05T12:00:00")
    tracker.check_off("Test Habit", timestamp_iso="2026-01-05T12:00:00")

    completions = tracker.get_completions(habit.id)
    assert completions == ["2026-01-05T12:00:00"]