"""results_table.py - how a results table is laid out, shared by the window and the web page.

Every table has Place, Sail number, Class, Name and two columns per race day (Heats: the races
sailed that day, and Points) under "Race" and the day's date, then the totals for its kind:

    Current results   Races, Points (all races), Average (points per race)
    Final results     Heats and Points under "All races", then under "Best 20" (if only the
                      best 20 count; otherwise just Races, Points)

Like a race day's two columns, the final table's grouped totals share a heading (the group).
"""

from __future__ import annotations

from ..model.results import ALL, CURRENT, FINAL, CompetitorResult, Results


def total_columns(results: Results) -> list[tuple[str, str, str]]:
    """(id, heading, group) for the columns after the race days; group "": a column of its own."""
    if results.table == CURRENT:
        return [("races", "Races", ""), ("total", "Points", ""), ("average", "Average", "")]
    if results.race_count:
        best = f"Best {results.race_count}"
        return [("races", "Heats", "All races"), ("total", "Points", "All races"),
                ("best_races", "Heats", best), ("points", "Points", best)]
    return [("races", "Races", ""), ("points", "Points", "")]


def day_dates(results: Results) -> list[str]:
    """Each race day's date, short ('09-10'), for a narrow heading; its name if not known."""
    dates = results.day_dates or [None] * len(results.day_names)
    return [f"{date.day:02d}-{date.month}" if date else name
            for name, date in zip(results.day_names, dates)]


def total_groups(columns: list[tuple[str, str, str]]) -> list[tuple[str, list[str]]]:
    """(group, column ids) for each run of columns: one per column where group is ""."""
    groups: list[tuple[str, list[str]]] = []
    for column_id, _, group in columns:
        if group and groups and groups[-1][0] == group:
            groups[-1][1].append(column_id)
        else:
            groups.append((group, [column_id]))
    return groups


def total_values(result: CompetitorResult, race_count: int | None = None) -> dict[str, str]:
    """Each total column's value; race_count: how many races count (None: all)."""
    best = min(result.races, race_count) if race_count else result.races
    return {"races": str(result.races), "total": str(result.total), "best_races": str(best),
            "points": str(result.points), "average": f"{float(result.average):.2f}"}


def results_note(results: Results) -> str:
    """A line saying how the table is ranked ("" if there is nothing to say)."""
    note = []
    if results.table == CURRENT:
        note.append("Ranked by average points per race sailed, however many races.")
        if results.race_count:
            note.append(f"Final results will count each boat's best {results.race_count} races.")
    elif results.table == FINAL and results.race_count:
        note.append(f"Only sailors who have sailed {results.race_count} races or more, ranked by "
                    f"their best {results.race_count}.")
        if results.left_out:
            sailors = "sailor has" if results.left_out == 1 else "sailors have"
            note.append(f"{results.left_out} {sailors} not sailed enough races yet.")
    elif results.race_count and results.table in (ALL, FINAL):
        note.append(f"Each boat's best {results.race_count} races count.")
    return " ".join(note)
