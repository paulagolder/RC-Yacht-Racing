"""sailor.py - one club sailor's boat: sail number, boat class, name and club.

A sailor may have several boats (several sail numbers) in a class. They can only sail one at a
time, so in results their sail numbers are alternatives: the same competitor (person_key).

Each sailor has a tag, a short code that tells them apart when sailors in different classes have
the same sail number ("12/PAG", see sail_entry.py). It defaults to their initials ("PG") and can
be changed to anything of up to MAX_TAG letters or digits ("PAG", "PGU") if initials clash.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .boat_class import class_key
from .sail_number import sail_key

DEFAULT_CLUB = "RMBC"
MAX_TAG = 4


def default_tag(forename: str, surname: str) -> str:
    """The sailor's initials: 'Paul', 'Gale' -> 'PG'."""
    return "".join(part.strip()[:1] for part in (forename, surname) if part.strip()).upper()


@dataclass(frozen=True)
class Sailor:
    sail_number: str        # as written in the members file, perhaps with leading spaces
    boat_class: str
    forename: str
    surname: str
    club: str = DEFAULT_CLUB
    tag: str = ""           # blank: the initials

    def __post_init__(self):
        tag = self.tag.strip().upper() or default_tag(self.forename, self.surname)
        object.__setattr__(self, "tag", tag)

    @property
    def name(self) -> str:
        return f"{self.forename} {self.surname}".strip()

    @property
    def number(self) -> str:
        """The sail number without its padding, for showing on screen."""
        return self.sail_number.strip()

    @property
    def key(self) -> tuple[str, str]:
        """Two sailors with the same key are the same boat."""
        return class_key(self.boat_class), sail_key(self.sail_number)

    @property
    def person_key(self) -> tuple[str, str]:
        """The same sailor in the same class, whichever of their boats: class and name, ignoring
        case and spacing. (Two different sailors with the same name in a class are not told apart.)"""
        return class_key(self.boat_class), self.same_person

    def problem(self) -> str | None:
        """What is missing from this sailor, or None if nothing is."""
        if not (self.number and self.boat_class.strip()):
            return "A sail needs a sail number and a boat class."
        if not self.name:
            return "A sail needs the sailor's forename or surname."
        if not re.fullmatch(rf"[A-Z0-9]{{1,{MAX_TAG}}}", self.tag):
            return f"A sailor's tag must be 1 to {MAX_TAG} letters or digits, such as PG or PAG."
        return None

    @property
    def same_person(self) -> str:
        """The sailor's name, ignoring case and spacing: the same person in any class."""
        return " ".join(self.name.split()).casefold()
