import sqlite3
from typing import List, Optional
from abc import ABC, abstractmethod

from .models import Habit


class Storage(ABC):
    """Abstract storage layer."""

    @abstractmethod
    def init_db(self) -> None: ...

    @abstractmethod
    def create_habit(self, habit: Habit) -> None: ...

    @abstractmethod
    def update_habit(self, habit: Habit) -> None: ...

    @abstractmethod
    def delete_habit(self, habit_id_or_name: str) -> bool: ...

    @abstractmethod
    def list_habits(self) -> List[Habit]: ...

    @abstractmethod
    def add_completion(self, habit_id: str, completed_at: str) -> None: ...

    @abstractmethod
    def list_completions(self, habit_id: str) -> List[str]: ...

    @abstractmethod
    def get_habit_by_name(self, name: str) -> Optional[Habit]: ...

    @abstractmethod
    def get_habit_by_id(self, habit_id: str) -> Optional[Habit]: ...

    @abstractmethod
    def get_meta(self, key: str) -> Optional[str]: ...

    @abstractmethod
    def set_meta(self, key: str, value: str) -> None: ...


class SQLiteStorage(Storage):
    """SQLite implementation of the Storage interface."""

    def __init__(self, db_path: str = "habits.db") -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        return con

    def init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS habits(
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    periodicity TEXT NOT NULL CHECK (periodicity IN ('daily','weekly')),
                    created_at TEXT NOT NULL
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS completions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
                );
                """
            )
            # Ensures identical fixture timestamps cannot duplicate
            con.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_completion_unique
                ON completions(habit_id, completed_at);
                """
            )
            # For idempotent seeding flag
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS app_meta(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            con.commit()

    def create_habit(self, habit: Habit) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO habits(id, name, periodicity, created_at) VALUES (?,?,?,?)",
                (habit.id, habit.name, habit.periodicity, habit.created_at),
            )
            con.commit()

    def update_habit(self, habit: Habit) -> None:
        """Update an existing habit identified by its id."""
        with self._connect() as con:
            con.execute(
                "UPDATE habits SET name = ?, periodicity = ? WHERE id = ?",
                (habit.name, habit.periodicity, habit.id),
            )
            con.commit()

    def delete_habit(self, habit_id_or_name: str) -> bool:
        key = (habit_id_or_name or "").strip()
        if not key:
            return False
        with self._connect() as con:
            cur = con.execute("DELETE FROM habits WHERE id = ?", (key,))
            if cur.rowcount == 0:
                cur = con.execute("DELETE FROM habits WHERE LOWER(name) = LOWER(?)", (key,))
            con.commit()
            return cur.rowcount > 0

    def list_habits(self) -> List[Habit]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT id, name, periodicity, created_at FROM habits ORDER BY name"
            ).fetchall()
            return [Habit.from_row(dict(r)) for r in rows]

    def add_completion(self, habit_id: str, completed_at: str) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO completions(habit_id, completed_at) VALUES (?,?)",
                (habit_id, completed_at),
            )
            con.commit()

    def list_completions(self, habit_id: str) -> List[str]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT completed_at FROM completions WHERE habit_id = ? ORDER BY completed_at",
                (habit_id,),
            ).fetchall()
            return [r["completed_at"] for r in rows]

    def get_habit_by_name(self, name: str) -> Optional[Habit]:
        name = (name or "").strip()
        if not name:
            return None
        with self._connect() as con:
            row = con.execute(
                "SELECT id, name, periodicity, created_at FROM habits WHERE LOWER(name) = LOWER(?)",
                (name,),
            ).fetchone()
            return Habit.from_row(dict(row)) if row else None

    def get_habit_by_id(self, habit_id: str) -> Optional[Habit]:
        habit_id = (habit_id or "").strip()
        if not habit_id:
            return None
        with self._connect() as con:
            row = con.execute(
                "SELECT id, name, periodicity, created_at FROM habits WHERE id = ?",
                (habit_id,),
            ).fetchone()
            return Habit.from_row(dict(row)) if row else None

    def get_meta(self, key: str) -> Optional[str]:
        with self._connect() as con:
            row = con.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT INTO app_meta(key, value) VALUES (?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            con.commit()
