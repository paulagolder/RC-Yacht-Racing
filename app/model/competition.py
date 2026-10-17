"""competition.py - a competition: its details, and up to MAX_RACE_DAYS race days.

    name        shown as the title, and gives the file name ("DF65 2026" -> DF65_2026.cxml)
    year
    classes     the ids (keys in yachtclasses.xml) of the boat classes that race, such as
                ["df65", "victoria"]; every race day is open to all of them
    clubs       only sailors from these clubs may race (none listed: any club)
    race_count  each boat's best race_count races count towards its points (None: all of them)
    directory   the sub folder of the output folder that Export HTML writes into
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field

from .boat_class import class_key
from .limits import MAX_RACE_DAYS, MAX_YEAR, MIN_YEAR
from .race_day import RaceDay, dated_name


def safe_file_name(text: str, fallback: str) -> str:
    """Text made safe for a file or folder name: 'DF65 / IOM' -> 'DF65_IOM'."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_.") or fallback


def split_list(text: str) -> list[str]:
    """'df65, victoria' -> ['df65', 'victoria']."""
    return [part.strip() for part in text.split(",") if part.strip()]


@dataclass
class Competition:
    name: str
    year: int
    classes: list[str]
    clubs: list[str] = field(default_factory=list)
    race_count: int | None = None
    directory: str = ""
    race_days: list[RaceDay] = field(default_factory=list)

    def __post_init__(self):
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValueError("A competition needs a name.")
        if (isinstance(self.year, bool) or not isinstance(self.year, int)
                or not MIN_YEAR <= self.year <= MAX_YEAR):
            raise ValueError(f"The year must be a whole number between {MIN_YEAR} and {MAX_YEAR}.")
        self.classes = _unique([str(c).strip() for c in self.classes])
        if not self.classes:
            raise ValueError("A competition needs at least one boat class, for example DF95.")
        self.clubs = _unique([str(c).strip() for c in self.clubs])
        if self.race_count is not None and (isinstance(self.race_count, bool)
                                            or not isinstance(self.race_count, int)
                                            or self.race_count < 1):
            raise ValueError("The number of races counted must be a whole number of at least 1.")
        self.directory = safe_file_name((self.directory or "").strip() or self.name, "competition")
        if len(self.race_days) > MAX_RACE_DAYS:
            raise ValueError(f"A competition can have at most {MAX_RACE_DAYS} race days.")

    @property
    def title(self) -> str:
        return self.name

    @property
    def is_full(self) -> bool:
        return len(self.race_days) >= MAX_RACE_DAYS

    def has_class(self, boat_class: str) -> bool:
        return class_key(boat_class) in {class_key(c) for c in self.classes}

    def next_race_day_name(self, date: datetime.date | None = None) -> str:
        """A default name that no existing race day is using: 'Race Day 30-12-1978' for a date
        ('Race Day 30-12-1978 (2)' if that is taken), or else 'Race day 3'."""
        taken = {d.name for d in self.race_days}
        if date is not None:
            name, n = dated_name(date), 2
            candidate = name
            while candidate in taken:
                candidate, n = f"{name} ({n})", n + 1
            return candidate
        n = len(self.race_days) + 1
        while f"Race day {n}" in taken:
            n += 1
        return f"Race day {n}"

    def add_race_day(self, day: RaceDay) -> int:
        """Add a race day at the end and return its index. Raises ValueError if it does not fit."""
        if self.is_full:
            raise ValueError(f"A competition can have at most {MAX_RACE_DAYS} race days.")
        self.race_days.append(day)
        return len(self.race_days) - 1

    def replace_race_day(self, index: int, day: RaceDay) -> None:
        self.race_days[index] = day

    def remove_race_day(self, index: int) -> RaceDay:
        return self.race_days.pop(index)

    def with_details(self, details: Competition) -> Competition:
        """A copy with the name, year, classes, clubs, race count and directory of details,
        and this competition's race days."""
        return Competition(details.name, details.year, details.classes, details.clubs,
                           details.race_count, details.directory, self.race_days)

    def same_details(self, other: Competition) -> bool:
        return ((self.name, self.year, self.classes, self.clubs, self.race_count, self.directory)
                == (other.name, other.year, other.classes, other.clubs, other.race_count,
                    other.directory))


def _unique(names: list[str]) -> list[str]:
    """Without blanks, and without repeats (ignoring case and spaces), in the order given."""
    seen, result = set(), []
    for name in names:
        if name and class_key(name) not in seen:
            seen.add(class_key(name))
            result.append(name)
    return result
