"""race_day.py - one day's racing: a name and up to MAX_RACES races.

On screen and in the file a race day is a table: one column per race, one row per finishing
place. columns, rows and from_table() give that view of the races.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .limits import DEFAULT_RACES, MAX_PLACES, MAX_RACES
from .race import Race, race_name


def default_races(count: int = DEFAULT_RACES) -> list[Race]:
    return [Race(race_name(i)) for i in range(1, count + 1)]


@dataclass
class RaceDay:
    name: str
    races: list[Race] = field(default_factory=default_races)

    def __post_init__(self):
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValueError("A race day needs a name.")
        self.set_races(self.races)

    @classmethod
    def from_table(cls, name: str, columns, rows) -> RaceDay:
        """A race day from a table: column names, and rows of cells (row 1 = 1st place)."""
        day = cls(name)
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
