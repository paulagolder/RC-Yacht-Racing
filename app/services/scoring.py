"""scoring.py - working out a competition's results so far.

Each finish scores Race.points(place) (1st = 1 point, 2nd = 2 ...), so fewer points is better.
A boat's points are the sum of its best competition.race_count races (all of them if the
competition does not say), over every race day. A competitor is a club sailor in a class: the
sailor with that sail number in one of the competition's classes (the first one, if several).
A sailor with several boats sails one at a time, so their sail numbers are alternatives and
all their races count together. A sail number that is no club sailor's is a competitor of its
own, with a blank class.

competition_results gives every boat, ranked by points. From it:

    current_results(results)   every boat, by average points per race (fewest first; on equal
                               averages, the boat with more races first)
    final_results(results)     only boats with at least race_count races, by their points
"""

from __future__ import annotations

from ..model.boat_class import class_key
from ..model.competition import Competition
from ..model.member_list import MemberList
from ..model.race import Race
from ..model.results import CURRENT, FINAL, CompetitorResult, Results
from ..model.sail_number import sail_key, sort_key


def competition_results(competition: Competition, members: MemberList | None = None,
                        classes: list[str] | None = None) -> Results:
    """Every boat in every race day so far, fewest points first (then by class and sail number).

    classes are the competition's classes as the club sailors' file names them (their full
    names); by default, competition.classes.
    """
    classes = list(classes or competition.classes)
    days = competition.race_days
    found: dict[tuple[str, str], CompetitorResult] = {}
    for d, day in enumerate(days):
        for race in day.races:
            for place, number in race.places():
                sailors = members.find_in(number, classes, competition.clubs) if members else []
                sailor = sailors[0] if sailors else None
                boat_class = _class_name(sailor.boat_class, classes) if sailor else ""
                key = sailor.person_key if sailor else ("", sail_key(number))
                shown = sailor.number if sailor else number.strip()
                result = found.get(key)
                if result is None:
                    result = CompetitorResult(shown, boat_class,
                                              sailor.name if sailor else "", [None] * len(days))
                    found[key] = result
                elif sail_key(shown) not in {sail_key(n) for n in
                                             [result.sail_number, *result.other_sail_numbers]}:
                    result.other_sail_numbers.append(shown)
                points = Race.points(place)
                result.day_points[d] = (result.day_points[d] or 0) + points
                result.race_points.append(points)
    for result in found.values():
        result.points = sum(sorted(result.race_points)[:competition.race_count])
    competitors = sorted(found.values(), key=lambda r: (r.points, class_key(r.boat_class),
                                                        sort_key(r.sail_number)))
    return Results([day.label for day in days], competition.race_count, competitors)


def current_results(results: Results) -> Results:
    """Every boat, ranked by its average points per race sailed."""
    competitors = sorted(results.competitors, key=lambda r: (r.average, -r.races,
                                                             class_key(r.boat_class),
                                                             sort_key(r.sail_number)))
    return Results(results.day_names, results.race_count, competitors, CURRENT)


def final_results(results: Results) -> Results:
    """Only the boats that have sailed the qualifying number of races (race_count; with no
    race_count every boat qualifies), ranked by their points as in results."""
    needed = results.race_count or 0
    competitors = [r for r in results.competitors if r.races >= needed]
    return Results(results.day_names, results.race_count, competitors, FINAL,
                   left_out=len(results.competitors) - len(competitors))


def _class_name(boat_class: str, classes: list[str]) -> str:
    """The class as written in classes ('VICTORIA' -> 'Victoria')."""
    return next((c for c in classes if class_key(c) == class_key(boat_class)), boat_class)
