"""html_export.py - a race day's table as a web page. No GUI code here.

    path = export_race_day_html(folder, club_title=..., competition_title=..., day_name=...,
                                columns=..., rows=..., members=..., boat_class=...)

The page is a single file (styles and club logo included), so it can be emailed, put on a
website or printed as it is. Each sail number is shown with its sailor's name when known.
Exporting the same race day again replaces its page.
"""

from __future__ import annotations

import base64
import datetime
import html
import re
from pathlib import Path

from .members import MemberList
from .settings import LOGO_FILE
from .storage import StorageError

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
.sail { font-weight: bold; }
.name { display: block; font-size: 0.85em; color: #555; }
footer { margin-top: 1.2em; font-size: 0.8em; color: #777; }
@media print { body { margin: 0; } th { background: #ddd; color: #000; } }
"""


def race_day_filename(day_name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", day_name).strip("_") or "race_day"
    return f"{safe}.html"


def _logo_tag() -> str:
    try:
        data = base64.b64encode(LOGO_FILE.read_bytes()).decode("ascii")
    except OSError:
        return ""
    return f'<img src="data:image/png;base64,{data}" alt="">'


def _cell(value: str, members: MemberList | None, boat_class: str) -> str:
    value = value.strip()
    if not value:
        return "<td></td>"
    sailor = members.find(value, boat_class) if members is not None else None
    name = f'<span class="name">{html.escape(sailor.name)}</span>' if sailor else ""
    return f'<td><span class="sail">{html.escape(value)}</span>{name}</td>'


def race_day_html(*, club_title: str, competition_title: str, day_name: str, columns: list[str],
                  rows: list[list[str]], members: MemberList | None = None, boat_class: str = "",
                  generated: datetime.datetime | None = None) -> str:
    generated = generated or datetime.datetime.now()
    e = html.escape
    head = "".join(f"<th>{e(name)}</th>" for name in columns)
    body = "\n".join(
        f'<tr><td class="row">{number}</td>'
        + "".join(_cell(value, members, boat_class) for value in row) + "</tr>"
        for number, row in enumerate(rows, start=1))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(competition_title)} - {e(day_name)}</title>
<style>{STYLE}</style>
</head>
<body>
<header>
{_logo_tag()}
<div>
<h1>{e(competition_title)}</h1>
<h2>{e(day_name)}</h2>
</div>
</header>
<table>
<thead><tr><th>Row</th>{head}</tr></thead>
<tbody>
{body}
</tbody>
</table>
<footer>{e(club_title)} &middot; {generated:%d %B %Y %H:%M}</footer>
</body>
</html>
"""


def export_race_day_html(folder, *, day_name: str, **page) -> Path:
    """Write the page into folder (made if needed) and return its path. Raises StorageError."""
    folder = Path(folder)
    path = folder / race_day_filename(day_name)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        path.write_text(race_day_html(day_name=day_name, **page), encoding="utf-8")
    except OSError as exc:
        raise StorageError(f"Could not write {path}: {exc.strerror or exc}") from exc
    return path
