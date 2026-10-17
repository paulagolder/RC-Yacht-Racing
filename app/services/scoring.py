"""scoring.py - working out a competition's results so far.

Each finish scores Race.points(place) (1st = 1 point, 2nd = 2 ...), so fewer points is better.
A boat's points are the sum of its best competition.race_count races (all of them if the
competition does not say), over every race day. A boat's class is its race day's class; on a
day open to all the competition's classes, it is the class of the club sailor with that sail
number (the first one, if several), or blank if there is none.
"""

from __future__ import annotations

from ..model.boat_class import class_key
from ..model.competition import Competition
from ..model.member_list import MemberList
from ..model.race import Race
from ..model.results import CompetitorResult, Results
from ..model.sail_number import sail_key, sort_key


def competition_results(competition: Competition, members: MemberList | None = None) -> Results:
    """Every boat in every race day so far, fewest points first (then by class and sail number)."""
    days = competition.race_days
    found: dict[tuple[str, str], CompetitorResult] = {}
    for d, day in enumerate(days):
        classes = competition.day_classes(day)
        for race in day.races:
            for place, number in race.places():
                sailors = members.find_in(number, classes, competition.clubs) if members else []
                sailor = sailors[0] if sailors else None
                boat_class = competition.class_name(day.boat_class
                                                    or (sailor.boat_class if sailor else ""))
                key = (class_key(boat_class), sail_key(number))
                result = found.get(key)
                if result is None:
                    result = CompetitorResult(sailor.number if sailor else number, boat_class,
                                              sailor.name if sailor else "", [None] * len(days))
                    found[key] = result
                points = Race.points(place)
                result.day_points[d] = (result.day_points[d] or 0) + points
                result.race_points.append(points)
    for result in found.values():
        result.points = sum(sorted(result.race_points)[:competition.race_count])
    competitors = sorted(found.values(), key=lambda r: (r.points, class_key(r.boat_class),
                                                        sort_key(r.sail_number)))
    return Results([day.name for day in days], competition.race_count, competitors)
