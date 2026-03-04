from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class Habit:
    """Represents a habit definition.

    This object stores the *definition* of a habit (name + periodicity).
    Actual completion events are stored separately in the database as timestamps,
    because a habit can be completed many times over its lifetime.
    """

    id: str
    name: str
    periodicity: str  # expected values: "daily" or "weekly"
    created_at: str  # ISO-8601 string (UTC)

    @staticmethod
    def from_row(row: Mapping[str, Any]) -> "Habit":
        """Create a Habit from a DB row/dict-like object.

        We keep this as a tiny adapter so the storage layer can remain simple:
        it can return raw SQLite rows/dicts, and we convert them into domain
        objects at the edges.
        """
        return Habit(
            id=row["id"],
            name=row["name"],
            periodicity=row["periodicity"],
            created_at=row["created_at"],
        )