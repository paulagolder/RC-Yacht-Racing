"""results.py - a competition's results so far: each boat's races and points.

Worked out by services/scoring.py. A boat is a sail number in a class: the same sail number in
two classes is two boats.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CompetitorResult:
    sail_number: str                 # as shown on screen, without padding
    boat_class: str
    name: str                        # "" if the sail number is not in the club list
    day_points: list[int | None]     # one per race day: points that day, None if not sailed
    race_points: list[int] = field(default_factory=list)   # every race sailed, in order
    points: int = 0                  # the races that count (see Results.race_count)

    @property
    def races(self) -> int:
        return len(self.race_points)

    @property
    def total(self) -> int:
        """Points from every race, counted or not."""
        return sum(self.race_points)


@dataclass
class Results:
    day_names: list[str]
    race_count: int | None = None    # best this many races count; None: all of them
    competitors: list[CompetitorResult] = field(default_factory=list)
