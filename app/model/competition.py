"""competition.py - a competition: one boat class in one year, with up to MAX_RACE_DAYS race days."""

from __future__ import annotations

from dataclasses import dataclass, field

from .limits import MAX_RACE_DAYS, MAX_YEAR, MIN_YEAR
from .race_day import RaceDay


@dataclass
class Competition:
    boat_class: str
    year: int
    race_days: list[RaceDay] = field(default_factory=list)

    def __post_init__(self):
        self.boat_class = (self.boat_class or "").strip()
        if not self.boat_class:
            raise ValueError("A competition needs a boat class, for example DF95.")
        if (isinstance(self.year, bool) or not isinstance(self.year, int)
                or not MIN_YEAR <= self.year <= MAX_YEAR):
            raise ValueError(f"The year must be a whole number between {MIN_YEAR} and {MAX_YEAR}.")
        if len(self.race_days) > MAX_RACE_DAYS:
            raise ValueError(f"A competition can have at most {MAX_RACE_DAYS} race days.")

    @property
    def title(self) -> str:
        return f"{self.boat_class} {self.year}"

    @property
    def is_full(self) -> bool:
        return len(self.race_days) >= MAX_RACE_DAYS

    def next_race_day_name(self) -> str:
        """A default name ('Race day 3') that no existing race day is using."""
        taken = {d.name for d in self.race_days}
        n = len(self.race_days) + 1
        while f"Race day {n}" in taken:
            n += 1
        return f"Race day {n}"

    def add_race_day(self, day: RaceDay) -> int:
        """Add a race day at the end and return its index. Raises ValueError if there is no room."""
        if self.is_full:
            raise ValueError(f"A competition can have at most {MAX_RACE_DAYS} race days.")
        self.race_days.append(day)
        return len(self.race_days) - 1

    def replace_race_day(self, index: int, day: RaceDay) -> None:
        self.race_days[index] = day

    def remove_race_day(self, index: int) -> RaceDay:
        return self.race_days.pop(index)
