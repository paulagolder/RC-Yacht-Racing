"""session.py - an open competition file.

Every change is saved to the file straight away ("after editing the competition file is
updated"). If a change cannot be saved, or is invalid, it is undone in memory as well and the
error is raised, so what is on screen never differs from what is in the file.
"""

from __future__ import annotations

from pathlib import Path

from ..model.competition import Competition
from ..model.race_day import RaceDay
from ..storage.competition_store import load_competition, save_competition
from ..storage.errors import StorageError


class CompetitionSession:
    def __init__(self, competition: Competition, path):
        self.competition = competition
        self.path = Path(path)

    # -- opening and creating -------------------------------------------------------------

    @classmethod
    def open(cls, path) -> CompetitionSession:
        """Open an existing competition file. Raises StorageError."""
        return cls(load_competition(path), path)

    @classmethod
    def create(cls, competition: Competition, path) -> CompetitionSession:
        """Write a new competition file and open it. Raises StorageError."""
        save_competition(competition, path)
        return cls(competition, path)

    # -- changes (each one is saved immediately) -----------------------------------------

    def add_race_day(self, day: RaceDay) -> int:
        """Add a race day and return its index. Raises ValueError or StorageError (nothing changed)."""
        index = self.competition.add_race_day(day)
        try:
            self._save()
        except StorageError:
            self.competition.remove_race_day(index)
            raise
        return index

    def update_race_day(self, index: int, day: RaceDay) -> None:
        """Replace a race day. Raises StorageError (nothing changed)."""
        old = self.competition.race_days[index]
        self.competition.replace_race_day(index, day)
        try:
            self._save()
        except StorageError:
            self.competition.replace_race_day(index, old)
            raise

    def delete_race_day(self, index: int) -> None:
        """Remove a race day. Raises StorageError (nothing changed)."""
        day = self.competition.remove_race_day(index)
        try:
            self._save()
        except StorageError:
            self.competition.race_days.insert(index, day)
            raise

    def _save(self) -> None:
        save_competition(self.competition, self.path)
