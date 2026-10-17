"""html_export.py - a race day's table, or a competition's results, as a web page.

    path = export_race_day_html(folder, race_day, club_title=..., competition_title=...,
                                resolver=...)
    path = export_results_html(folder, results, club_title=..., competition_title=...)
                                    # results_current.html or results_final.html
    path = export_results_html(folder, results, abridged=True, ...)
                                    # the totals only: results_current_abridged.html ...

resolver (a sail_entry.SailResolver, CompetitionSession.resolver) knows the competition's classes
and finds the sailor each entry means.

Each page is a single file (styles and club logo included), so it can be emailed, put on a
website or printed as it is. On a race day's page each sail number is shown with its sailor's
name when known. Exporting the same race day (or the results) again replaces its page.
"""

from __future__ import annotations

import base64
import datetime
import html
import re
from pathlib import Path

from ..model.race_day import RaceDay
from ..model.results import ALL, Results
from ..model.sail_entry import SailResolver
from ..storage.errors import StorageError
from ..storage.settings_store import LOGO_FILE
from .results_table import day_dates, results_note, total_columns, total_groups, total_values

STYLE = """
body { font-family: "Segoe UI", Arial, sans-serif; color: #222; margin: 2em; }
header { display: flex; align-items: center; gap: 16px; margin-bottom: 1.2em; }
header img { height: 64px; }
h1 { font-size: 1.6em; margin: 0; }
h2 { font-size: 1.2em; margin: 0.2em 0 0; color: #444; font-weight: normal; }
table { border-collapse: collapse; }
th, td { border: 1px solid #bbb; padding: 4px 12px; text-align: left; vertical-align: top; }
th { background: #4d5962; color: #fff; }
tbody tr:nth-child(even) { background: #f2f4f6; }
td.row { text-align: center; font-weight: bold; color: #555; }
th.day { text-align: center; padding: 4px 6px; line-height: 1.2; }
th.sub { text-align: center; padding: 2px 6px; font-size: 0.75em; font-weight: normal; }
td.num, td.heats { text-align: center; padding: 4px 6px; }
td.heats { color: #777; }
td.points { text-align: center; font-weight: bold; }
p.note { margin: 0 0 0.8em; color: #555; }
.sail { font-weight: bold; }
.name { display: block; font-size: 0.85em; color: #555; }
footer { margin-top: 1.2em; font-size: 0.8em; color: #777; }
@media print { body { margin: 0; } th { background: #ddd; color: #000; } }
"""


def results_filename(results: Results, abridged: bool = False) -> str:
    """results_current.html or results_final.html (results.html for the table of every boat);
    results_current_abridged.html ... for the table without the race days."""
    name = f"results_{results.table}" if results.table != ALL else "results"
    return f"{name}_abridged.html" if abridged else f"{name}.html"


def race_day_filename(day_name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", day_name).strip("_") or "race_day"
    return f"{safe}.html"


def _logo_tag() -> str:
    try:
        data = base64.b64encode(LOGO_FILE.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f'<img src="data:image/png;base64,{data}" alt="">'


def _cell(value: str, resolver: SailResolver | None) -> str:
    value = value.strip()
    if not value:
        return "<td></td>"
    sailor = resolver.sailor(value) if resolver is not None else None
    name = f'<span class="name">{html.escape(sailor.name)}</span>' if sailor else ""
    return f'<td><span class="sail">{html.escape(value)}</span>{name}</td>'


def race_day_html(race_day: RaceDay, *, club_title: str, competition_title: str,
                  resolver: SailResolver | None = None,
                  generated: datetime.datetime | None = None) -> str:
    generated = generated or datetime.datetime.now()
    e = html.escape
    day_name = race_day.label
    classes = resolver.class_names if resolver is not None else []
    subtitle = f"{e(day_name)} &middot; {e(', '.join(classes))}" if classes else e(day_name)
    head = "".join(f"<th>{e(name)}</th>" for name in race_day.columns)
    body = "\n".join(
        f'<tr><td class="row">{number}</td>'
        + "".join(_cell(value, resolver) for value in row) + "</tr>"
        for number, row in enumerate(race_day.rows, start=1))
    table = f"<thead><tr><th>Row</th>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>"
    return _page(f"{competition_title} - {day_name}", competition_title, subtitle, "", table,
                 club_title, generated)


def results_html(results: Results, *, club_title: str, competition_title: str,
                 abridged: bool = False, generated: datetime.datetime | None = None) -> str:
    """The results table (current or final): place, boat, heats and points each race day, and
    totals. Abridged: without the race days."""
    generated = generated or datetime.datetime.now()
    e = html.escape
    totals = total_columns(results)
    headings = {column_id: heading for column_id, heading, _ in totals}
    grouped = {column_id for column_id, _, group in totals if group}
    dates = [] if abridged else day_dates(results)
    span = ' rowspan="2"' if dates or grouped else ""     # over the Heats / Points row
    head = ("<tr>" + "".join(f"<th{span}>{heading}</th>" for heading in
                             ("Place", "Sail numbers", "Name"))
            + "".join(f'<th colspan="2" class="day">Race<br>{e(date)}</th>' for date in dates)
            + "".join(f'<th colspan="{len(ids)}" class="day">{e(group)}</th>' if group else
                      f"<th{span}>{e(headings[ids[0]])}</th>"
                      for group, ids in total_groups(totals))
            + "</tr>")
    if span:
        head += ("\n<tr>" + '<th class="sub">Heats</th><th class="sub">Points</th>' * len(dates)
                 + "".join(f'<th class="sub">{e(heading)}</th>'
                           for _, heading, group in totals if group)
                 + "</tr>")
    last = totals[-1][0]                                    # what the table is ranked by
    rows = []
    for place, r in zip(results.places(), results.competitors):
        heats = r.day_races or [""] * len(r.day_points)
        days = "" if abridged else "".join(
            f'<td class="heats"></td><td class="num"></td>' if p is None else
            f'<td class="heats">{h}</td><td class="num">{p}</td>'
            for h, p in zip(heats, r.day_points))
        values = total_values(r, results.race_count)
        sums = "".join(f'<td class="{_total_class(headings[c], c == last)}">{values[c]}</td>'
                       for c, _, _ in totals)
        rows.append(f'<tr><td class="row">{place}</td><td class="sail">{e(r.sail_numbers)}</td>'
                    f"<td>{e(r.name)}</td>{days}{sums}</tr>")
    if not rows:
        columns = 3 + 2 * len(dates) + len(totals)
        rows.append(f'<tr><td colspan="{columns}">No results yet.</td></tr>')
    table = f"<thead>{head}</thead>\n<tbody>\n" + "\n".join(rows) + "\n</tbody>"
    title = f"{results.title} at {generated.day} {generated:%B %Y}"   # which day's table it is
    note = results_note(results)
    return _page(f"{competition_title} - {title}", competition_title, e(title),
                 f'<p class="note">{e(note)}</p>' if note else "", table, club_title, generated)


def _total_class(heading: str, ranked_by: bool) -> str:
    """Bold for what the table is ranked by; grey for heats, as on the race days."""
    return "points" if ranked_by else "heats" if heading == "Heats" else "num"


def _page(title: str, heading: str, subtitle: str, before_table: str, table: str,
          club_title: str, generated: datetime.datetime) -> str:
    """A whole page; subtitle, before_table and table are HTML already, the rest is text."""
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<header>
{_logo_tag()}
<div>
<h1>{e(heading)}</h1>
<h2>{subtitle}</h2>
</div>
</header>
{before_table}<table>
{table}
</table>
<footer>{e(club_title)} &middot; {generated:%d %B %Y %H:%M}</footer>
</body>
</html>
"""


def export_race_day_html(folder, race_day: RaceDay, **page) -> Path:
    """Write the page into folder (made if needed) and return its path. Raises StorageError."""
    return _write(Path(folder) / race_day_filename(race_day.name), race_day_html(race_day, **page))


def export_results_html(folder, results: Results, abridged: bool = False, **page) -> Path:
    """Write the results page (abridged: without the race days) into folder (made if needed)
    and return its path. Raises StorageError."""
    return _write(Path(folder) / results_filename(results, abridged),
                  results_html(results, abridged=abridged, **page))


def _write(path: Path, text: str) -> Path:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"Could not write {path}: {exc.strerror or exc}") from exc
    return path
