"""summary.py - a short account of a competition so far, for the report.

Worked out by services/report.py from the competition and its results.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DaySummary:
    name: str
    races: int               # races in the table
    races_sailed: int        # races with at least one finisher
    finishes: int            # sail numbers entered
    boats: int               # different boats that took part


@dataclass
class Leader:
    """One of the leading boats in the current results (by average points per race)."""
    place: int
    sail_number: str
    boat_class: str
    name: str
    average: float
    races: int


@dataclass
class CompetitionSummary:
    name: str
    year: int
    classes: list[str]                          # full names
    clubs: list[str]                            # none: any club
    race_count: int | None                      # best this many races count; None: all
    max_race_days: int
    days: list[DaySummary] = field(default_factory=list)
    competitors: int = 0                        # different boats over the whole competition
    by_class: dict[str, int] = field(default_factory=dict)   # class ("": not a club sailor) -> boats
    leaders: list[Leader] = field(default_factory=list)      # the first few places
    qualified: int | None = None                # boats with race_count races or more (None: no count)

    @property
    def races(self) -> int:
        return sum(d.races for d in self.days)

    @property
    def races_sailed(self) -> int:
        return sum(d.races_sailed for d in self.days)

    @property
    def finishes(self) -> int:
        return sum(d.finishes for d in self.days)
