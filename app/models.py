"""models.py - the data model. No GUI code here, so it can be tested without a screen.

A Competition (boat class + year) holds up to 15 RaceDays.
A RaceDay is a small table: up to 6 columns and 15 rows of text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_COLUMNS = 6      # widest table
MAX_ROWS = 15        # longest table
MAX_RACE_DAYS = 15   # race days (tables) in one competition
DEFAULT_COLUMNS = 4  # columns a new race day starts with (the editor can add up to MAX_COLUMNS)
DEFAULT_ROWS = 5     # rows the editor shows for an empty race day
                     # (both can be changed in ~/.pyraceresults/properties.xml, see settings.py)
MIN_YEAR, MAX_YEAR = 1900, 2200


def letters(n: int) -> str:
    """1 -> A, 2 -> B ... 26 -> Z, 27 -> AA."""
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def column_label(n: int) -> str:
    """1 -> 'Race A', 2 -> 'Race B', ..."""
    return f"Race {letters(n)}"


def default_columns(count: int = DEFAULT_COLUMNS) -> list[str]:
    return [column_label(i) for i in range(1, count + 1)]


def next_cell_position(row: int, col: int, n_rows: int, n_cols: int,
                       max_rows: int = MAX_ROWS) -> tuple[int, int, bool]:
    """Where Enter/Tab goes next: down the column.

    Returns (row, col, add_row). add_row is True when the target row does not exist
    yet and the table is still allowed to grow. At the bottom of a full table the
    cursor moves to the top of the next column (wrapping from the last column to the first).
    """
    if row + 1 < n_rows:
        return row + 1, col, False
    if n_rows < max_rows:
        return row + 1, col, True
    return 0, (col + 1) % n_cols, False


def previous_cell_position(row: int, col: int, n_rows: int, n_cols: int) -> tuple[int, int]:
    """Where Shift+Tab / Up goes: up the column, or to the bottom of the previous column."""
    if row > 0:
        return row - 1, col
    return n_rows - 1, (col - 1) % n_cols


@dataclass
class RaceDay:
    name: str
    columns: list[str] = field(default_factory=default_columns)
    rows: list[list[str]] = field(default_factory=list)

    def __post_init__(self):
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValueError("A race day needs a name.")
        self.set_table(self.columns, self.rows)

    def set_table(self, columns, rows) -> None:
        """Replace the table. Validates first, so a failed call leaves the old table unchanged.

        Every cell is stored as text, short rows are padded, and empty rows at the end are dropped.
        """
        columns = [str(c) for c in columns]
        if not 1 <= len(columns) <= MAX_COLUMNS:
            raise ValueError(
                f"A race day needs between 1 and {MAX_COLUMNS} columns (got {len(columns)})."
            )

        cleaned = []
        for number, row in enumerate(rows, start=1):
            cells = [str(c) for c in row]
            if any(c.strip() for c in cells[len(columns):]):
                raise ValueError(f"Row {number} has more cells than there are columns.")
            cells = cells[: len(columns)]
            cells += [""] * (len(columns) - len(cells))
            cleaned.append(cells)

        while cleaned and not any(c.strip() for c in cleaned[-1]):
            cleaned.pop()
        if len(cleaned) > MAX_ROWS:
            raise ValueError(f"A race day can have at most {MAX_ROWS} rows (got {len(cleaned)}).")

        self.columns = columns
        self.rows = cleaned


@dataclass
class Competition:
    boat_class: str
    year: int
    race_days: list[RaceDay] = field(default_factory=list)

    def __post_init__(self):
        self.boat_class = (self.boat_class or "").strip()
        if not self.boat_class:
            raise ValueError("A competition needs a boat class, for example DF95.")
        if (isinstance(self.year, bool) or not isinstance(self.year, int)
                or not MIN_YEAR <= self.year <= MAX_YEAR):
            raise ValueError(f"The year must be a whole number between {MIN_YEAR} and {MAX_YEAR}.")
        if len(self.race_days) > MAX_RACE_DAYS:
            raise ValueError(f"A competition can have at most {MAX_RACE_DAYS} race days.")

    @property
    def title(self) -> str:
        return f"{self.boat_class} {self.year}"

    def next_race_day_name(self) -> str:
        """A default name ('Race day 3') that no existing race day is using."""
        taken = {d.name for d in self.race_days}
        n = len(self.race_days) + 1
        while f"Race day {n}" in taken:
            n += 1
        return f"Race day {n}"

    def add_race_day(self, name: str | None = None) -> RaceDay:
        if len(self.race_days) >= MAX_RACE_DAYS:
            raise ValueError(f"A competition can have at most {MAX_RACE_DAYS} race days.")
        day = RaceDay(name or self.next_race_day_name())
        self.race_days.append(day)
        return day

    def rename_race_day(self, index: int, name: str) -> None:
        name = (name or "").strip()
        if not name:
            raise ValueError("A race day needs a name.")
        self.race_days[index].name = name

    def remove_race_day(self, index: int) -> None:
        del self.race_days[index]
