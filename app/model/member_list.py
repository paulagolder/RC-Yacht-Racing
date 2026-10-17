"""member_list.py - the club's sailors (RMBCSail.xml), one per boat.

Race results are checked against them by sail_entry.SailResolver.
"""

from __future__ import annotations

from pathlib import Path

from .boat_class import class_key
from .sail_number import sail_key
from .sailor import Sailor


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
            if i == ignore:
                continue
            if other.key == sailor.key:
                return f"{other.name} already has {other.boat_class} sail number {other.number}."
            if (sail_key(other.sail_number) == sail_key(sailor.sail_number)
                    and other.same_person != sailor.same_person and other.tag == sailor.tag):
                return (f"{other.name} ({other.boat_class} {other.number}) has the same sail number "
                        f"and tag {other.tag}. Give one of them a different tag, such as "
                        f"{sailor.forename[:2].upper()}{sailor.surname[:1].upper()}, so their "
                        "results can be told apart.")
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
