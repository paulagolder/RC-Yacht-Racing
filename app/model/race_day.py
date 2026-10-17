"""race_day.py - one day's racing: a name, a date and up to MAX_RACES races.

Every race day is open to all of its competition's classes: a sailor in any of them may race.
The date may be unknown (None), as it is for race days entered before dates were kept. On
screen dates are day/month/year: parse_date() reads what is typed and format_date() shows it.
A race day with a date but no name is named from the date: "Race Day 30-12-1978".

On screen and in the file a race day is a table: one column per race, one row per finishing
place. columns, rows and from_table() give that view of the races.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field

from .limits import DEFAULT_RACES, MAX_PLACES, MAX_RACES
from .race import Race, race_name


DATE_FORMAT = "%d/%m/%Y"                 # 10/10/2026
_DATE_FORMATS = (DATE_FORMAT, "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y")


def default_races(count: int = DEFAULT_RACES) -> list[Race]:
    return [Race(race_name(i)) for i in range(1, count + 1)]


def parse_date(text: str) -> datetime.date | None:
    """'10/10/2026', '10-10-26' or '2026-10-10' -> a date; blank -> None. Raises ValueError."""
    text = (text or "").strip()
    if not text:
        return None
    for date_format in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(text, date_format).date()
        except ValueError:
            pass
    raise ValueError(f"'{text}' is not a date. Type it as day/month/year, for example 10/10/2026.")


def format_date(date: datetime.date | None) -> str:
    return date.strftime(DATE_FORMAT) if date else ""


def dated_name(date: datetime.date) -> str:
    """The default name for a race day on this date: 'Race Day 30-12-1978'."""
    return f"Race Day {date:%d-%m-%Y}"


def is_dated_name(name: str) -> bool:
    """Whether a name is one made from a date ('Race Day 30-12-1978', perhaps with ' (2)')."""
    return re.fullmatch(r"Race Day \d\d-\d\d-\d{4}( \(\d+\))?", name.strip()) is not None


@dataclass
class RaceDay:
    name: str
    races: list[Race] = field(default_factory=default_races)
    date: datetime.date | None = None        # None: not known

    def __post_init__(self):
        if self.date is not None and not isinstance(self.date, datetime.date):
            raise ValueError("A race day's date must be a date.")
        self.name = (self.name or "").strip() or (dated_name(self.date) if self.date else "")
        if not self.name:
            raise ValueError("A race day needs a name or a date.")
        self.set_races(self.races)

    @property
    def label(self) -> str:
        """The name and date, for lists and headings: 'Spring open (10/10/2026)'. A name made
        from the date already says it, so it is shown on its own."""
        if not self.date or self.name.startswith(dated_name(self.date)):
            return self.name
        return f"{self.name} ({format_date(self.date)})"

    @classmethod
    def from_table(cls, name: str, columns, rows, date: datetime.date | None = None) -> RaceDay:
        """A race day from a table: column names, and rows of cells (row 1 = 1st place)."""
        day = cls(name, date=date)
        day.set_table(columns, rows)
        return day

    # -- the table view ---------------------------------------------------------------------

    @property
    def columns(self) -> list[str]:
        return [race.name for race in self.races]

    @property
    def rows(self) -> list[list[str]]:
        return [list(row) for row in zip(*(race.finishers for race in self.races))]

    def set_table(self, columns, rows) -> None:
        """Replace the races from a table. Raises ValueError, leaving the old races unchanged.

        Every cell is stored as text, short rows are padded, and empty rows at the end are dropped.
        """
        columns = [str(c) for c in columns]
        if not 1 <= len(columns) <= MAX_RACES:
            raise ValueError(
                f"A race day needs between 1 and {MAX_RACES} races (got {len(columns)})."
            )
        cells = []
        for number, row in enumerate(rows, start=1):
            row = [str(c) for c in row]
            if any(c.strip() for c in row[len(columns):]):
                raise ValueError(f"Row {number} has more cells than there are races.")
            cells.append(row[: len(columns)] + [""] * (len(columns) - len(row)))
        self.set_races([Race(name, [row[c] for row in cells]) for c, name in enumerate(columns)])

    # -- the races --------------------------------------------------------------------------

    def set_races(self, races: list[Race]) -> None:
        """Replace the races. Raises ValueError, leaving the old races unchanged.

        Every race is given the same number of places, and empty places after the last
        finisher in any race are dropped.
        """
        if not 1 <= len(races) <= MAX_RACES:
            raise ValueError(f"A race day needs between 1 and {MAX_RACES} races (got {len(races)}).")
        length = max(len(race.finishers) for race in races)
        while length and not any(race.finishers[length - 1].strip() for race in races
                                 if len(race.finishers) >= length):
            length -= 1
        if length > MAX_PLACES:
            raise ValueError(f"A race day can have at most {MAX_PLACES} rows (got {length}).")
        self.races = [Race(race.name, (race.finishers + [""] * length)[:length]) for race in races]
