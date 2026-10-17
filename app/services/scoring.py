"""scoring.py - working out a competition's results so far.

Each finish scores Race.points(place) (1st = 1 point, 2nd = 2 ...), so fewer points is better.
A competitor's total is the sum over every race on every race day.
"""

from __future__ import annotations

from ..model.competition import Competition
from ..model.member_list import MemberList
from ..model.race import Race
from ..model.results import CompetitorResult, Results
from ..model.sail_number import sail_key, sort_key


def competition_results(competition: Competition, members: MemberList | None = None) -> Results:
    """Every competitor in every race day so far, fewest points first (then in sail number order)."""
    days = competition.race_days
    found: dict[str, CompetitorResult] = {}
    for d, day in enumerate(days):
        for race in day.races:
            for place, number in race.places():
                key = sail_key(number)
                result = found.get(key)
                if result is None:
                    sailor = members.find(number, competition.boat_class) if members else None
                    result = CompetitorResult(sailor.number if sailor else number,
                                              sailor.name if sailor else "", [None] * len(days))
                    found[key] = result
                points = Race.points(place)
                result.day_points[d] = (result.day_points[d] or 0) + points
                result.races += 1
                result.points += points
    competitors = sorted(found.values(), key=lambda r: (r.points, sort_key(r.sail_number)))
    return Results([day.name for day in days], competitors)
