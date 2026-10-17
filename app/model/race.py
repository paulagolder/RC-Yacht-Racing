"""race.py - one race: its name and who finished where.

A race lists the sail numbers of its finishers in finishing order: finishers[0] came 1st.
A place may be left empty (""), and the places after it keep their numbers. Each finish
scores as many points as its place (1st = 1 point, 2nd = 2 ...), so fewer points is better.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field


def letters(n: int) -> str:
    """1 -> A, 2 -> B ... 26 -> Z, 27 -> AA."""
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def race_name(n: int) -> str:
    """The default name of the nth race in a day: 1 -> 'Race A', 2 -> 'Race B' ..."""
    return f"Race {letters(n)}"


@dataclass
class Race:
    name: str
    finishers: list[str] = field(default_factory=list)   # sail numbers, 1st place first; "" = empty

    def __post_init__(self):
        self.name = str(self.name)
        self.finishers = [str(f) for f in self.finishers]

    def places(self) -> Iterator[tuple[int, str]]:
        """(place, sail number) for every finish, skipping empty places."""
        for place, sail_number in enumerate(self.finishers, start=1):
            if sail_number.strip():
                yield place, sail_number.strip()

    @staticmethod
    def points(place: int) -> int:
        """Points for finishing in this place."""
        return place
