import sqlite3

import pytest

from habit_tracker.storage import SQLiteStorage


def test_init_db_creates_tables_indexes_and_fk_cascade(db_path):
    """init_db() should set up the expected schema and constraints.

    We verify:
    - required tables exist
    - the unique index for completions exists
    - completions has a FK to habits with ON DELETE CASCADE
    """
    storage = SQLiteStorage(db_path)
    storage.init_db()

    con = sqlite3.connect(db_path)
    try:
        # --- Tables ---
        table_rows = con.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = {row[0] for row in table_rows}
        assert "habits" in table_names
        assert "completions" in table_names
        assert "app_meta" in table_names

        # --- Indexes ---
        index_rows = con.execute("SELECT name FROM sqlite_master WHERE type='index';").fetchall()
        index_names = {row[0] for row in index_rows}
        assert "ux_completion_unique" in index_names

        # --- Foreign key constraints on completions ---
        # PRAGMA foreign_key_list(<table>) shows FK rules, including the ON DELETE action.
        fk_rows = con.execute("PRAGMA foreign_key_list(completions);").fetchall()
        assert len(fk_rows) >= 1

        # Row format: (id, seq, table, from, to, on_update, on_delete, match)
        fk = fk_rows[0]
        assert fk[2] == "habits"        # referenced table
        assert fk[3] == "habit_id"      # FK column in completions
        assert fk[4] == "id"            # PK column in habits
        assert fk[6].upper() == "CASCADE"
    finally:
        con.close()


def test_connect_enables_foreign_keys_per_connection(db_path):
    """SQLite requires PRAGMA foreign_keys=ON per connection.

    Our SQLiteStorage._connect() helper should ensure it is enabled so that
    ON DELETE CASCADE actually works.
    """
    storage = SQLiteStorage(db_path)
    storage.init_db()

    con = storage._connect()  # testing an internal helper is fine for storage behavior
    try:
        foreign_keys_enabled = con.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert foreign_keys_enabled == 1
    finally:
        con.close()


def test_deleting_habit_cascades_its_completions(tracker):
    """Deleting a habit should also delete its completion rows (ON DELETE CASCADE)."""
    habit = tracker.add_habit("Cascade Habit", "daily")
    tracker.check_off("Cascade Habit", timestamp_iso="2026-01-05T12:00:00")
    tracker.check_off("Cascade Habit", timestamp_iso="2026-01-06T12:00:00")

    assert tracker.get_completions(habit.id) == [
        "2026-01-05T12:00:00",
        "2026-01-06T12:00:00",
    ]

    assert tracker.delete_habit("Cascade Habit") is True

    # After deletion, completions should be gone as well.
    assert tracker.get_completions(habit.id) == []


def test_unique_index_prevents_duplicate_completion_timestamps(tracker):
    """Same completion timestamp for the same habit should not be stored twice."""
    habit = tracker.add_habit("Unique Completion Habit", "daily")

    tracker.check_off("Unique Completion Habit", timestamp_iso="2026-01-05T12:00:00")
    tracker.check_off("Unique Completion Habit", timestamp_iso="2026-01-05T12:00:00")

    # The unique index + INSERT OR IGNORE should keep only one row.
    assert tracker.get_completions(habit.id) == ["2026-01-05T12:00:00"]


def test_get_habit_by_name_is_case_insensitive(storage):
    """get_habit_by_name should not care about name casing."""
    storage.init_db()

    # Insert directly via storage (bypassing tracker), so we test storage behavior in isolation.
    from habit_tracker.models import Habit

    habit = Habit(
        id="H1",
        name="Read Book",
        periodicity="daily",
        created_at="2026-01-01T00:00:00",
    )
    storage.create_habit(habit)

    found = storage.get_habit_by_name("read book")
    assert found is not None
    assert found.id == "H1"
    assert found.name == "Read Book"


def test_delete_habit_by_name_is_case_insensitive(storage):
    """delete_habit should accept keys in different casing."""
    storage.init_db()

    from habit_tracker.models import Habit

    habit = Habit(
        id="H2",
        name="Drink Water",
        periodicity="daily",
        created_at="2026-01-01T00:00:00",
    )
    storage.create_habit(habit)

    assert storage.delete_habit("drink water") is True
    assert storage.get_habit_by_id("H2") is None


def test_app_meta_set_and_update(storage):
    """set_meta should behave like an upsert: insert if missing, update if present."""
    storage.init_db()

    assert storage.get_meta("fixture_seeded") is None

    storage.set_meta("fixture_seeded", "true")
    assert storage.get_meta("fixture_seeded") == "true"

    storage.set_meta("fixture_seeded", "false")
    assert storage.get_meta("fixture_seeded") == "false"