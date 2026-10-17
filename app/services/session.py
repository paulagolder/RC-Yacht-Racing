"""session.py - an open competition file, and the boat classes it is read with.

When a file is opened its classes are normalised to class ids (keys in yachtclasses.xml), so
a file written as classes="Victoria,DF65" is treated as ["df65", "victoria"]. A class that is
not in yachtclasses.xml is kept as it is.

Every change is saved to the file straight away ("after editing the competition file is
updated"). If a change cannot be saved, or is invalid, it is undone in memory as well and the
error is raised, so what is on screen never differs from what is in the file.
"""

from __future__ import annotations

from pathlib import Path

from ..model.boat_class import DEFAULT_BOAT_CLASSES, BoatClass, BoatClassList
from ..model.competition import Competition
from ..model.member_list import MemberList
from ..model.race_day import RaceDay
from ..model.sail_entry import SailResolver
from ..storage.competition_store import load_competition, save_competition
from ..storage.errors import StorageError


class CompetitionSession:
    def __init__(self, competition: Competition, path, boat_classes: BoatClassList | None = None):
        self.competition = competition
        self.path = Path(path)
        self.boat_classes = boat_classes or BoatClassList(DEFAULT_BOAT_CLASSES)
        try:
            competition.classes = self.boat_classes.normalise(competition.classes)
        except ValueError:
            pass                    # a class that is not in yachtclasses.xml: leave them as written

    @property
    def class_names(self) -> list[str]:
        """The competition's classes by their full names, for the screen and for finding sailors."""
        return self.boat_classes.display_names(self.competition.classes)

    @property
    def class_objects(self) -> list[BoatClass]:
        """The competition's classes from yachtclasses.xml (one that is not there: just its id)."""
        return [self.boat_classes.find(c) or BoatClass(c, c) for c in self.competition.classes]

    def resolver(self, members: MemberList | None) -> SailResolver:
        """Reads the competition's sail entries against these club sailors."""
        return SailResolver(members, self.class_objects, self.competition.clubs)

    # -- opening and creating -------------------------------------------------------------

    @classmethod
    def open(cls, path, boat_classes: BoatClassList | None = None) -> CompetitionSession:
        """Open an existing competition file. Raises StorageError."""
        return cls(load_competition(path), path, boat_classes)

    @classmethod
    def create(cls, competition: Competition, path,
               boat_classes: BoatClassList | None = None) -> CompetitionSession:
        """Write a new competition file and open it. Raises StorageError."""
        save_competition(competition, path)
        return cls(competition, path, boat_classes)

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
