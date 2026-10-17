"""member_list.py - the club's sailors, and checking race results against them.

Every sail number in a race must belong to a sailor in the race day's classes from the
competition's clubs, and may only appear once in each race.
"""

from __future__ import annotations

from pathlib import Path

from .boat_class import class_key
from .race import Race
from .sail_number import sail_key
from .sailor import Sailor

Problem = tuple[int, int, str]      # (row, race index, message), counting from 0


class MemberList:
    def __init__(self, sailors: list[Sailor] | None = None, path: Path | None = None):
        self.sailors: list[Sailor] = list(sailors or [])
        self.path = path            # the file the list was read from, if any
        self._reindex()

    def _reindex(self) -> None:
        self._index = {s.key: s for s in self.sailors}

    def __len__(self) -> int:
        return len(self.sailors)

    # -- finding ----------------------------------------------------------------------------

    def find(self, sail_number: str, boat_class: str, clubs: list[str] | None = None) -> Sailor | None:
        """The sailor with this sail number in this class, or None.

        Given clubs, only a sailor from one of them is found (none listed: any club).
        """
        sailor = self._index.get((class_key(boat_class), sail_key(sail_number)))
        if sailor is not None and clubs and class_key(sailor.club) not in {class_key(c) for c in clubs}:
            return None
        return sailor

    def find_in(self, sail_number: str, classes: list[str],
                clubs: list[str] | None = None) -> list[Sailor]:
        """Every sailor with this sail number in any of these classes (from clubs, if given)."""
        found = (self.find(sail_number, boat_class, clubs) for boat_class in classes)
        return list(dict.fromkeys(s for s in found if s is not None))

    def boat_classes(self) -> list[str]:
        """Every class in the list, as first written, in alphabetical order."""
        return sorted({s.boat_class for s in self.sailors}, key=str.upper)

    # -- changing ---------------------------------------------------------------------------

    def check(self, sailor: Sailor, ignore: int | None = None) -> str | None:
        """Why this sailor cannot be added (or replace sailors[ignore]), or None if it can."""
        problem = sailor.problem()
        if problem:
            return problem
        for i, other in enumerate(self.sailors):
            if i != ignore and other.key == sailor.key:
                return f"{other.name} already has {other.boat_class} sail number {other.number}."
        return None

    def add(self, sailor: Sailor) -> None:
        """Raises ValueError (with the reason) if the sailor cannot be added."""
        problem = self.check(sailor)
        if problem:
            raise ValueError(problem)
        self.sailors.append(sailor)
        self._reindex()

    def replace(self, index: int, sailor: Sailor) -> None:
        """Raises ValueError (with the reason) if the sailor cannot replace sailors[index]."""
        problem = self.check(sailor, ignore=index)
        if problem:
            raise ValueError(problem)
        self.sailors[index] = sailor
        self._reindex()

    def remove(self, index: int) -> Sailor:
        sailor = self.sailors.pop(index)
        self._reindex()
        return sailor

    # -- checking results -------------------------------------------------------------------

    def check_races(self, races: list[Race], classes: list[str],
                    clubs: list[str] | None = None) -> list[Problem]:
        """Problems in a race day's results, in table order. Empty places are allowed.

        A finish is wrong if its sail number is not that of a sailor in one of classes (from
        one of clubs, if given), if the same sail number is already further up the same race,
        or if the sailor is already further up the race with another of their boats (a sailor
        sails one boat at a time). A number that is a sailor's in more than one of the classes
        is accepted for now.
        """
        from_clubs = f" from {', '.join(clubs)}" if clubs else ""
        problems = []
        for c, race in enumerate(races):
            seen: dict[str, int] = {}             # sail number -> row first seen
            sailing: dict[tuple[str, str], tuple[int, str]] = {}   # person -> (row, sail number)
            for place, value in race.places():
                r = place - 1
                sailors = self.find_in(value, classes, clubs)
                if not sailors:
                    problems.append((r, c, f"No {' or '.join(classes)} sailor{from_clubs} has "
                                           f"sail number '{value}'."))
                    continue
                if sail_key(value) in seen:
                    problems.append((r, c, f"Sail number '{value}' is already in row "
                                           f"{seen[sail_key(value)] + 1} of this race."))
                    continue
                seen[sail_key(value)] = r
                sailor = sailors[0]
                if sailor.person_key in sailing:
                    row, number = sailing[sailor.person_key]
                    problems.append((r, c, f"{sailor.name} is already sailing {number.strip()} in "
                                           f"row {row + 1} of this race."))
                else:
                    sailing[sailor.person_key] = (r, value)
        return sorted(problems)
