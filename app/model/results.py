"""results.py - a competition's results so far: each boat's races and points.

Worked out by services/scoring.py. A competitor is a club sailor in a class, whichever of their
boats (sail numbers) they sailed; a sail number that is not a club sailor's is a competitor of its
own. The same sail number in two classes is two competitors. There are two tables:

    CURRENT   every boat, ranked by its average points per race sailed, however many races
              it has sailed. Fair enough during the season, when not everyone can make every
              race day.
    FINAL     only the boats that have sailed the qualifying number of races (the competition's
              race_count), ranked by the points from their best race_count races.

ALL is every boat ranked by its points, the table the other two are made from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

ALL = "all"
CURRENT = "current"
FINAL = "final"

TITLES = {ALL: "Results", CURRENT: "Current results", FINAL: "Final results"}


@dataclass
class CompetitorResult:
    sail_number: str                 # the first one sailed, as shown on screen (no padding)
    boat_class: str
    name: str                        # "" if the sail number is not in the club list
    day_points: list[int | None]     # one per race day: points that day, None if not sailed
    race_points: list[int] = field(default_factory=list)   # every race sailed, in order
    points: int = 0                  # the races that count (see Results.race_count)
    other_sail_numbers: list[str] = field(default_factory=list)   # the sailor's other boats sailed

    @property
    def sail_numbers(self) -> str:
        """Every sail number sailed, for showing: '440 / 23'."""
        return " / ".join([self.sail_number, *self.other_sail_numbers])

    @property
    def races(self) -> int:
        return len(self.race_points)

    @property
    def total(self) -> int:
        """Points from every race, counted or not."""
        return sum(self.race_points)

    @property
    def average(self) -> Fraction:
        """Points per race sailed (exact, so equal averages are equal); 0 if none sailed."""
        return Fraction(self.total, self.races) if self.races else Fraction(0)


@dataclass
class Results:
    day_names: list[str]             # each race day's name and date (RaceDay.label)
    race_count: int | None = None    # best this many races count; None: all of them
    competitors: list[CompetitorResult] = field(default_factory=list)
    table: str = ALL                 # ALL, CURRENT or FINAL
    left_out: int = 0                # FINAL: boats with fewer than race_count races

    @property
    def title(self) -> str:
        return TITLES[self.table]

    def score(self, result: CompetitorResult) -> int | Fraction:
        """What the table is ranked by (fewer is better): average points, or points."""
        return result.average if self.table == CURRENT else result.points

    def places(self) -> list[int]:
        """Each competitor's place, in order: 1 for the best score; equal scores share a place."""
        found: list[int] = []
        for index, result in enumerate(self.competitors):
            tied = index and self.score(result) == self.score(self.competitors[index - 1])
            found.append(found[-1] if tied else index + 1)
        return found
