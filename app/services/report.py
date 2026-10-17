"""report.py - a text summary of a competition so far.

    text = summary_text(competition_summary(competition, results, class_names))

The summary gives the number of race days, races and finishes, how many different boats have
taken part (in each class), each race day's figures, how many boats have sailed enough races
for the final results, and the leading boats in the current results.
"""

from __future__ import annotations

import datetime

from ..model.competition import Competition
from ..model.limits import MAX_RACE_DAYS
from ..model.results import Results
from ..model.summary import CompetitionSummary, DaySummary, Leader
from .scoring import current_results, final_results

LEADERS = 3                 # how many of the leading places the report lists
NOT_A_CLUB_SAILOR = "not a club sailor"


def competition_summary(competition: Competition, results: Results,
                        class_names: list[str] | None = None) -> CompetitionSummary:
    """results are every boat's (scoring.competition_results). class_names are the
    competition's classes by their full names (default: as stored)."""
    summary = CompetitionSummary(competition.name, competition.year,
                                 list(class_names or competition.classes), list(competition.clubs),
                                 competition.race_count, MAX_RACE_DAYS)
    for d, day in enumerate(competition.race_days):
        finishes = [len(list(race.places())) for race in day.races]
        summary.days.append(DaySummary(
            day.label, len(day.races), sum(1 for f in finishes if f), sum(finishes),
            sum(1 for r in results.competitors if r.day_points[d] is not None)))
    summary.competitors = len(results.competitors)
    for r in results.competitors:
        summary.by_class[r.boat_class] = summary.by_class.get(r.boat_class, 0) + 1
    current = current_results(results)
    summary.leaders = [Leader(place, r.sail_number, r.boat_class, r.name, float(r.average), r.races)
                       for place, r in zip(current.places(), current.competitors)
                       if place <= LEADERS]
    if competition.race_count:
        summary.qualified = len(final_results(results).competitors)
    return summary
    return summary


def summary_text(summary: CompetitionSummary, generated: datetime.datetime | None = None) -> str:
    generated = generated or datetime.datetime.now()
    clubs = ", ".join(summary.clubs) or "any club"
    counted = (f"best {summary.race_count} races count" if summary.race_count
               else "every race counts")
    lines = [f"{summary.name} - competition report",
             f"{summary.year} · {', '.join(summary.classes)} · {clubs} · {counted}",
             f"Produced {generated:%d %B %Y %H:%M}",
             "",
             f"Race days:    {len(summary.days)} (of {summary.max_race_days})",
             f"Races sailed: {summary.races_sailed} (of {summary.races} in the tables)",
             f"Finishes:     {summary.finishes}",
             f"Competitors:  {summary.competitors} different boats"]
    for boat_class in sorted(summary.by_class, key=lambda c: (c == "", c.upper())):
        lines.append(f"    {boat_class or NOT_A_CLUB_SAILOR}: {summary.by_class[boat_class]}")
    if summary.qualified is not None:
        lines.append(f"Qualified:    {summary.qualified} with {summary.race_count} races or more "
                     "(in the final results)")

    if summary.days:
        width = max(len("Race day"), *(len(d.name) for d in summary.days))
        lines += ["", f"{'Race day':<{width}}  Races  Boats  Finishes"]
        lines += [f"{d.name:<{width}}  {d.races_sailed:>5}  {d.boats:>5}  {d.finishes:>8}"
                  for d in summary.days]
    else:
        lines += ["", "No race days yet."]

    if summary.leaders:
        lines += ["", "Leading the current results (average points per race):"]
        for leader in summary.leaders:
            who = " ".join(p for p in (leader.sail_number, f"({leader.boat_class})"
                                       if leader.boat_class else "", leader.name) if p)
            lines.append(f"  {leader.place}. {who}: {leader.average:.2f} over {leader.races} "
                         f"race{'s' if leader.races != 1 else ''}")
    return "\n".join(lines) + "\n"
