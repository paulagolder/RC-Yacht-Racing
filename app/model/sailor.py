"""sailor.py - one club sailor's boat: sail number, boat class, name and club.

A sailor may have several boats (several sail numbers) in a class. They can only sail one at a
time, so in results their sail numbers are alternatives: the same competitor (person_key).
"""

from __future__ import annotations

from dataclasses import dataclass

from .boat_class import class_key
from .sail_number import sail_key

DEFAULT_CLUB = "RMBC"


@dataclass(frozen=True)
class Sailor:
    sail_number: str        # as written in the members file, perhaps with leading spaces
    boat_class: str
    forename: str
    surname: str
    club: str = DEFAULT_CLUB

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
        return class_key(self.boat_class), " ".join(self.name.split()).casefold()

    def problem(self) -> str | None:
        """What is missing from this sailor, or None if nothing is."""
        if not (self.number and self.boat_class.strip()):
            return "A sail needs a sail number and a boat class."
        if not self.name:
            return "A sail needs the sailor's forename or surname."
        return None
