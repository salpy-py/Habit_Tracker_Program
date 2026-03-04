import uuid
from datetime import date, timedelta
from typing import List, Optional, Tuple

from .models import Habit
from .storage import Storage
from .time_utils import now_utc_iso, local_datetime_to_utc_iso
from . import analytics

# Supported habit periodicities (portfolio requirement).
VALID_PERIODS = ("daily", "weekly")

DEFAULT_HABITS = [
    ("Drink 2L water", "daily"),
    ("Read 20 minutes", "daily"),
    ("Walk 6000 steps", "daily"),
    ("Gym session", "weekly"),
    ("Clean/organize room", "weekly"),
]


class HabitTracker:
    """Application service layer: validation + storage + analytics."""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.storage.init_db()

    def add_habit(self, name: str, periodicity: str) -> Habit:
        name = (name or "").strip()
        if not name:
            raise ValueError("Habit name cannot be empty.")
        p = (periodicity or "").strip().lower()
        if p not in VALID_PERIODS:
            raise ValueError("Invalid periodicity. Use 'daily' or 'weekly'.")
        if self.storage.get_habit_by_name(name):
            raise ValueError(f"Habit already exists: {name}")

        habit = Habit(
            id=str(uuid.uuid4()),
            name=name,
            periodicity=p,
            created_at=now_utc_iso(),
        )
        self.storage.create_habit(habit)
        return habit

    def edit_habit(
        self,
        habit_id_or_name: str,
        new_name: Optional[str] = None,
        new_periodicity: Optional[str] = None,
    ) -> Habit:
        """Edit an existing habit (name and/or periodicity)."""
        habit = self._resolve_habit(habit_id_or_name)

        if new_name is None and new_periodicity is None:
            raise ValueError("Nothing to update. Provide --name and/or --period.")

        if new_name is not None:
            new_name = new_name.strip()
            if not new_name:
                raise ValueError("Habit name cannot be empty.")
            existing = self.storage.get_habit_by_name(new_name)
            if existing and existing.id != habit.id:
                raise ValueError(f"Habit already exists: {new_name}")
            habit.name = new_name

        if new_periodicity is not None:
            p = new_periodicity.strip().lower()
            if p not in VALID_PERIODS:
                raise ValueError("Invalid periodicity. Use 'daily' or 'weekly'.")
            habit.periodicity = p

        self.storage.update_habit(habit)
        return habit

    def delete_habit(self, habit_id_or_name: str) -> bool:
        return self.storage.delete_habit(habit_id_or_name)

    def get_habits(self) -> List[Habit]:
        return self.storage.list_habits()

    def _resolve_habit(self, habit_id_or_name: str) -> Habit:
        key = (habit_id_or_name or "").strip()
        if not key:
            raise ValueError("Habit identifier cannot be empty.")
        h = self.storage.get_habit_by_id(key) or self.storage.get_habit_by_name(key)
        if not h:
            raise ValueError(f"Habit not found: {habit_id_or_name}")
        return h

    def check_off(self, habit_id_or_name: str, timestamp_iso: str = None) -> None:
        """Record a completion; timestamp is stored as an ISO string."""
        h = self._resolve_habit(habit_id_or_name)
        ts = timestamp_iso or now_utc_iso()
        self.storage.add_completion(h.id, ts)

    def get_completions(self, habit_id: str) -> List[str]:
        return self.storage.list_completions(habit_id)

    def analyze_overview(self) -> List[Tuple[Habit, int, int]]:
        """Returns rows: (habit, current_streak, longest_streak)."""
        rows: List[Tuple[Habit, int, int]] = []
        for h in self.get_habits():
            comps = self.get_completions(h.id)
            rows.append(
                (
                    h,
                    analytics.current_streak_for(comps, h.periodicity),
                    analytics.longest_streak_for(comps, h.periodicity),
                )
            )
        return rows

    def analyze_longest_overall(self) -> Tuple[Optional[Habit], int]:
        return analytics.longest_streak_all(self.get_habits(), self.get_completions)

    def seed_fixture(self) -> str:
        """
        Inserts 5 predefined habits + 4 weeks fixture data.

        Notes:
        - Idempotent: if app_meta.fixture_seeded is true, seeding is skipped.
        - Intended for demo usage (not used by unit tests).
        """
        if self.storage.get_meta("fixture_seeded") == "true":
            return "Fixture already seeded. Skipping."

        # Create habits (safe insert due to UNIQUE name + INSERT OR IGNORE)
        for name, per in DEFAULT_HABITS:
            if not self.storage.get_habit_by_name(name):
                self.storage.create_habit(
                    Habit(
                        id=str(uuid.uuid4()),
                        name=name,
                        periodicity=per,
                        created_at=now_utc_iso(),
                    )
                )

        # Deterministic 28-day window ending yesterday
        today = date.today()
        start = today - timedelta(days=28)

        habits_by_name = {h.name: h for h in self.get_habits()}

        # Daily habits: complete Mon–Sat at 09:00 local, skip Sundays
        for i in range(28):
            d = start + timedelta(days=i)
            if d.weekday() == 6:  # Sunday
                continue
            ts = local_datetime_to_utc_iso(d, hour=9, minute=0)
            for habit_name, per in DEFAULT_HABITS:
                if per == "daily":
                    self.storage.add_completion(habits_by_name[habit_name].id, ts)

        # Weekly habits: complete each Monday at 10:00 local (4 times)
        for w in range(4):
            d = start + timedelta(days=w * 7)
            d = d - timedelta(days=d.weekday())  # Monday of that week
            ts = local_datetime_to_utc_iso(d, hour=10, minute=0)
            for habit_name, per in DEFAULT_HABITS:
                if per == "weekly":
                    self.storage.add_completion(habits_by_name[habit_name].id, ts)

        self.storage.set_meta("fixture_seeded", "true")
        return "Fixture seeded successfully."
