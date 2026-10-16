"""session.py - an open competition file. No GUI code here, so it can be tested without a screen.

Every change is saved to the file straight away ("after editing the competition file is
updated"). If a change cannot be saved, or is invalid, it is undone in memory as well and the
error is raised, so what is on screen never differs from what is in the file.
"""

from __future__ import annotations

from pathlib import Path

from .models import Competition
from .storage import StorageError, load_competition, save_competition


class CompetitionSession:
    def __init__(self, competition: Competition, path):
        self.competition = competition
        self.path = Path(path)

    # -- opening and creating -------------------------------------------------------------

    @classmethod
    def open(cls, path) -> "CompetitionSession":
        """Open an existing competition file. Raises StorageError."""
        return cls(load_competition(path), path)

    @classmethod
    def create(cls, competition: Competition, path) -> "CompetitionSession":
        """Write a new competition file and open it. Raises StorageError."""
        save_competition(competition, path)
        return cls(competition, path)

    # -- changes (each one is saved immediately) -----------------------------------------

    def add_race_day(self, name: str, columns, rows) -> int:
        """Add a race day and return its index. Raises ValueError or StorageError (nothing changed)."""
        days = self.competition.race_days
        day = self.competition.add_race_day(name)
        try:
            day.set_table(columns, rows)
            self._save()
        except (ValueError, StorageError):
            days.pop()
            raise
        return len(days) - 1

    def update_race_day(self, index: int, name: str, columns, rows) -> None:
        """Replace a race day's name and table. Raises ValueError or StorageError (nothing changed)."""
        day = self.competition.race_days[index]
        old_name, old_columns = day.name, list(day.columns)
        old_rows = [list(row) for row in day.rows]
        try:
            day.set_table(columns, rows)
            self.competition.rename_race_day(index, name)
            self._save()
        except (ValueError, StorageError):
            day.set_table(old_columns, old_rows)
            day.name = old_name
            raise

    def delete_race_day(self, index: int) -> None:
        """Remove a race day. Raises StorageError (nothing changed)."""
        days = self.competition.race_days
        day = days[index]
        del days[index]
        try:
            self._save()
        except StorageError:
            days.insert(index, day)
            raise

    def _save(self) -> None:
        save_competition(self.competition, self.path)
