"""results.py - a competition's results so far: each competitor's points and races.

Worked out by services/scoring.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CompetitorResult:
    sail_number: str                 # as shown on screen, without padding
    name: str                        # "" if the sail number is not in the club list
    day_points: list[int | None]     # one per race day: points that day, None if not sailed
    races: int = 0
    points: int = 0


@dataclass
class Results:
    day_names: list[str]
    competitors: list[CompetitorResult] = field(default_factory=list)
