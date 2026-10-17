"""results.py - the results of a competition so far. No GUI code here.

Each race day table lists the finishers of each race (column) in order: row 1 finished first.
A finish earns as many points as the finishing place, which is its row number (1st = 1 point,
2nd = 2, ...), so fewer points is better. Empty cells are skipped.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .members import MemberList, _sail_key
from .models import Competition


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


def _sort_key(sail_number: str) -> tuple:
    """Numbers in number order (2 before 10), then anything else."""
    key = _sail_key(sail_number)
    return (0, int(key), "") if key.isdigit() else (1, 0, key)


def competition_results(competition: Competition, members: MemberList | None = None) -> Results:
    """Every competitor in every race day so far, fewest points first (then in sail number order)."""
    days = competition.race_days
    found: dict[str, CompetitorResult] = {}
    for d, day in enumerate(days):
        for c in range(len(day.columns)):
            for place, row in enumerate(day.rows, start=1):
                number = row[c].strip()
                if not number:
                    continue
                key = _sail_key(number)
                result = found.get(key)
                if result is None:
                    sailor = members.find(number, competition.boat_class) if members else None
                    result = CompetitorResult(sailor.number if sailor else number,
                                              sailor.name if sailor else "", [None] * len(days))
                    found[key] = result
                result.day_points[d] = (result.day_points[d] or 0) + place
                result.races += 1
                result.points += place
    competitors = sorted(found.values(), key=lambda r: (r.points,_sort_key(r.sail_number)))
    return Results([day.name for day in days], competitors)
