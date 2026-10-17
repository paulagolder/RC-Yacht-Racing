"""results_table.py - how a results table is laid out, shared by the window and the web page.

Every table has Place, Sail number, Class, Name and one column per race day (the points that
day), then the totals for its kind:

    Current results   Races, Points (all races), Average (points per race)
    Final results     Races, All races (if only the best count), Points (the races that count)
"""

from __future__ import annotations

from ..model.results import ALL, CURRENT, FINAL, CompetitorResult, Results


def total_columns(results: Results) -> list[tuple[str, str]]:
    """(id, heading) for the columns after the race days."""
    if results.table == CURRENT:
        return [("races", "Races"), ("total", "Points"), ("average", "Average")]
    if results.race_count:
        return [("races", "Races"), ("total", "All races"), ("points", "Points")]
    return [("races", "Races"), ("points", "Points")]


def total_values(result: CompetitorResult) -> dict[str, str]:
    return {"races": str(result.races), "total": str(result.total),
            "points": str(result.points), "average": f"{float(result.average):.2f}"}


def results_note(results: Results) -> str:
    """A line saying how the table is scored."""
    note = "Points: 1st place = 1, 2nd = 2 ... (fewer is better)."
    if results.table == CURRENT:
        note += " Ranked by average points per race sailed, however many races."
        if results.race_count:
            note += f" Final results will count each boat's best {results.race_count} races."
    elif results.table == FINAL and results.race_count:
        note += (f" Only sailors who have sailed {results.race_count} races or more, ranked by "
                 f"their best {results.race_count}.")
        if results.left_out:
            sailors = "sailor has" if results.left_out == 1 else "sailors have"
            note += f" {results.left_out} {sailors} not sailed enough races yet."
    elif results.race_count and results.table in (ALL, FINAL):
        note += f" Each boat's best {results.race_count} races count."
    return note
