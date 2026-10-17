"""sailor.py - one club sailor's boat: sail number, boat class, name and club."""

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

    def problem(self) -> str | None:
        """What is missing from this sailor, or None if nothing is."""
        if not (self.number and self.boat_class.strip()):
            return "A sail needs a sail number and a boat class."
        if not self.name:
            return "A sail needs the sailor's forename or surname."
        return None
