"""race_day_window.py - the window for entering or editing one race day's table.

    edited = RaceDayWindow(parent, race_day).show()     # a new RaceDay, or None if cancelled

Enter, Tab and Down move down the column; at the bottom the table grows by a row until it
reaches MAX_PLACES, after which the cursor moves to the top of the next column. Shift+Tab and
Up go the other way. The window is modal: the window behind it is blocked until it closes.

The race day is open to all the competition's classes, which are shown but cannot be changed
here (change them in the competition's details). Each cell holds a sail number. Given a
MemberList, the window shows whose boat the current cell is, marks numbers that are not
sailors' in the competition's classes and clubs (or are repeated in a race), and will not
save until they are fixed.
"""

from __future__ import annotations

import csv
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..model.limits import DEFAULT_ROWS, MAX_PLACES, MAX_RACES
from ..model.member_list import MemberList, Problem
from ..model.race import Race, race_name
from ..model.race_day import RaceDay, dated_name, format_date, is_dated_name, parse_date
from ..services.html_export import export_race_day_html
from ..storage.errors import StorageError
from .browser import open_in_browser
from .grid_navigation import next_cell_position, previous_cell_position

BOLD = ("TkDefaultFont", 10, "bold")
BAD_STYLE = "Bad.TEntry"


def _without_trailing_blank_rows(rows: list[list[str]]) -> list[list[str]]:
    rows = [list(r) for r in rows]
    while rows and not any(c.strip() for c in rows[-1]):
        rows.pop()
    return rows


class RaceDayWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, race_day: RaceDay, title: str = "Edit race day",
                 default_rows: int = DEFAULT_ROWS, members: MemberList | None = None,
                 classes: list[str] | None = None, clubs: list[str] | None = None,
                 html_folder: Path | None = None, competition_title: str = "",
                 club_title: str = ""):
        super().__init__(parent)
        self._parent = parent
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.result: RaceDay | None = None
        self.members = members
        self.classes = list(classes or [])         # the competition's, by their full names
        self.clubs = list(clubs or [])
        self.html_folder = html_folder              # Export HTML writes here (None: no button)
        self.competition_title = competition_title
        self.club_title = club_title
        ttk.Style(self).configure(BAD_STYLE, fieldbackground="#f6c6c6", foreground="#9c0000")

        self.columns: list[str] = list(race_day.columns)    # race names
        self.cells: list[list[ttk.Entry]] = []     # cells[row][column]

        # Race day name and date
        top = ttk.Frame(self, padding=(12, 12, 12, 0))
        top.grid(row=0, column=0, sticky="w")
        ttk.Label(top, text="Race day name:").pack(side="left")
        self.name_var = tk.StringVar(value=race_day.name)
        self.name_entry = ttk.Entry(top, textvariable=self.name_var, width=24)
        self.name_entry.pack(side="left", padx=6)
        ttk.Label(top, text="Date:").pack(side="left", padx=(12, 0))
        self.date_var = tk.StringVar(value=format_date(race_day.date))
        self.date_entry = ttk.Entry(top, textvariable=self.date_var, width=11)
        self.date_entry.pack(side="left", padx=6)
        ttk.Label(top, text="dd/mm/yyyy", foreground="gray40").pack(side="left")
        self.date_var.trace_add("write", lambda *_: self._date_changed())
        if self.classes:
            ttk.Label(top, text="Classes:").pack(side="left", padx=(12, 0))
            ttk.Label(top, text=", ".join(self.classes), font=BOLD).pack(side="left", padx=6)

        # The table: headers in grid row 0, row numbers in grid column 0
        self.grid_frame = ttk.Frame(self, padding=12)
        self.grid_frame.grid(row=1, column=0)
        for c, name in enumerate(self.columns, start=1):
            self._make_header(c, name)
        for _ in range(max(min(default_rows, MAX_PLACES), len(race_day.rows))):
            self._build_row()
        for r, values in enumerate(race_day.rows):
            for c, value in enumerate(values):
                self.cells[r][c].insert(0, value)

        # Whose sail number the current cell is
        self.sailor_var = tk.StringVar()
        ttk.Label(self, textvariable=self.sailor_var, padding=(12, 0, 12, 8)).grid(
            row=2, column=0, sticky="w")

        # Buttons
        bar = ttk.Frame(self, padding=(12, 0, 12, 12))
        bar.grid(row=3, column=0)
        ttk.Button(bar, text="Save", command=self._save).pack(side="left", padx=4)
        ttk.Button(bar, text="Cancel", command=self._cancel).pack(side="left", padx=4)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=8)
        self.add_row_button = ttk.Button(bar, text="Add row", command=self.add_row)
        self.add_row_button.pack(side="left", padx=4)
        self.add_column_button = ttk.Button(bar, text="Add column", command=self.add_column)
        self.add_column_button.pack(side="left", padx=4)
        ttk.Button(bar, text="Clear", command=self._clear).pack(side="left", padx=4)
        ttk.Button(bar, text="Export CSV", command=self._export_csv).pack(side="left", padx=4)
        if html_folder is not None:
            ttk.Button(bar, text="Export HTML", command=self._export_html).pack(side="left", padx=4)
        self._update_buttons()

        # Keys
        for sequence in ("<Return>", "<KP_Enter>", "<Tab>", "<Down>"):
            self.bind(sequence, lambda e: self._move(e, forward=True))
        for sequence in ("<Up>", "<Shift-Tab>", "<ISO_Left_Tab>"):
            try:
                self.bind(sequence, lambda e: self._move(e, forward=False))
            except tk.TclError:          # a platform that has no such key name
                pass
        self.bind("<Escape>", lambda e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._initial = self._snapshot()

    # -- building the table -----------------------------------------------------------------

    def _make_header(self, grid_column: int, name: str) -> None:
        ttk.Label(self.grid_frame, text=name, font=BOLD).grid(
            row=0, column=grid_column, padx=4, pady=(0, 6))

    def _make_entry(self, grid_row: int, grid_column: int) -> ttk.Entry:
        entry = ttk.Entry(self.grid_frame, width=14)
        entry.grid(row=grid_row, column=grid_column, padx=4, pady=2)
        entry.bind("<FocusIn>", lambda e: self._show_sailor(entry), add="+")
        entry.bind("<KeyRelease>", lambda e: self._show_sailor(entry), add="+")
        entry.bind("<FocusOut>", lambda e: self._mark_problems(), add="+")
        return entry

    def _build_row(self) -> None:
        r = len(self.cells) + 1
        ttk.Label(self.grid_frame, text=str(r), font=BOLD).grid(row=r, column=0, padx=(0, 8))
        self.cells.append([self._make_entry(r, c) for c in range(1, len(self.columns) + 1)])

    def add_row(self) -> None:
        if len(self.cells) < MAX_PLACES:
            self._build_row()
            self._update_buttons()

    def add_column(self) -> None:
        if len(self.columns) >= MAX_RACES:
            return
        name = race_name(len(self.columns) + 1)
        self.columns.append(name)
        c = len(self.columns)
        self._make_header(c, name)
        for r, row in enumerate(self.cells, start=1):
            row.append(self._make_entry(r, c))
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.add_row_button.state(["!disabled" if len(self.cells) < MAX_PLACES else "disabled"])
        self.add_column_button.state(["!disabled" if len(self.columns) < MAX_RACES else "disabled"])

    # -- moving around ----------------------------------------------------------------------

    def _locate(self, widget: object) -> tuple[int, int] | None:
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                if cell is widget:
                    return r, c
        return None

    def _focus_cell(self, row: int, col: int) -> None:
        cell = self.cells[row][col]
        cell.focus_set()
        cell.select_range(0, tk.END)      # typing replaces what is there
        cell.icursor(tk.END)

    def _move(self, event: tk.Event, forward: bool) -> str | None:
        if event.widget is self.name_entry:
            if forward:                   # Enter in the name box starts the data entry
                self._focus_cell(0, 0)
                return "break"
            return None
        pos = self._locate(event.widget)
        if pos is None:                   # focus is on a button: leave the key alone
            return None
        row, col = pos
        n_rows, n_cols = len(self.cells), len(self.columns)
        if forward:
            row, col, grow = next_cell_position(row, col, n_rows, n_cols)
            if grow:
                self.add_row()
        else:
            row, col = previous_cell_position(row, col, n_rows, n_cols)
        self._focus_cell(row, col)
        return "break"                    # stop Tk's own left-to-right Tab order

    # -- reading the table ------------------------------------------------------------------

    def _values(self) -> list[list[str]]:
        return [[cell.get() for cell in row] for row in self.cells]

    def _races(self) -> list[Race]:
        """The table as races: one per column, finishers top to bottom."""
        return [Race(name, [row[c].get() for row in self.cells])
                for c, name in enumerate(self.columns)]

    def _date_changed(self) -> None:
        """A name that is blank or made from the date follows the date as it is typed."""
        name = self.name_var.get()
        if name.strip() and not is_dated_name(name):
            return
        try:
            date = parse_date(self.date_var.get())
        except ValueError:
            return                        # not a whole date yet
        if date is not None:
            self.name_var.set(dated_name(date))

    def _race_day(self, title: str) -> RaceDay | None:
        """The race day as entered, or None (after saying why) if its name or date is wrong."""
        try:
            date = parse_date(self.date_var.get())
        except ValueError as exc:
            messagebox.showwarning(title, str(exc), parent=self)
            self.date_entry.focus_set()
            return None
        try:
            return RaceDay(self.name_var.get(), self._races(), date)
        except ValueError as exc:
            messagebox.showwarning(title, str(exc), parent=self)
            self.name_entry.focus_set()
            return None

    def _snapshot(self) -> tuple:
        return (self.name_var.get(), self.date_var.get(), list(self.columns),
                _without_trailing_blank_rows(self._values()))

    # -- checking sail numbers -------------------------------------------------------------

    def _show_sailor(self, entry: ttk.Entry) -> None:
        if self.members is None:
            return
        classes = " or ".join(self.classes)
        value = entry.get().strip()
        sailors = self.members.find_in(value, self.classes, self.clubs) if value else []
        if not value:
            self.sailor_var.set(f"Enter a {classes} sail number.")
        elif sailors:
            self.sailor_var.set("; ".join(f"{s.number}: {s.name} ({s.boat_class}, {s.club})"
                                          for s in sailors))
        else:
            clubs = f" from {', '.join(self.clubs)}" if self.clubs else ""
            self.sailor_var.set(f"No {classes} sailor{clubs} has sail number '{value}'.")

    def _mark_problems(self) -> list[Problem]:
        """Colour the cells that are wrong, and return the problems."""
        if self.members is None:
            return []
        problems = self.members.check_races(self._races(), self.classes, self.clubs)
        bad = {(r, c) for r, c, _ in problems}
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                cell.configure(style=BAD_STYLE if (r, c) in bad else "TEntry")
        return problems

    # -- buttons ----------------------------------------------------------------------------

    def _save(self) -> None:
        day = self._race_day("Race day")
        if day is None:
            return
        problems = self._mark_problems()
        if problems:
            lines = [f"{self.columns[c]}, row {r + 1}: {message}" for r, c, message in problems[:8]]
            if len(problems) > 8:
                lines.append(f"... and {len(problems) - 8} more.")
            where = f"\n\nClub sailors are listed in {self.members.path}." if self.members.path else ""
            messagebox.showwarning("Sail numbers", "Please fix the marked cells:\n\n"
                                   + "\n".join(lines) + where, parent=self)
            self._focus_cell(problems[0][0], problems[0][1])
            return
        self.result = day
        self.destroy()

    def _cancel(self) -> None:
        if self._snapshot() != self._initial and not messagebox.askyesno(
                "Discard changes?", "Close without saving your changes?", parent=self):
            return
        self.destroy()

    def _clear(self) -> None:
        if any(cell.get().strip() for row in self.cells for cell in row):
            if not messagebox.askyesno("Clear table", "Clear every cell in this table?", parent=self):
                return
        for row in self.cells:
            for cell in row:
                cell.delete(0, tk.END)
        self._focus_cell(0, 0)

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile=f"{self.name_var.get().strip() or 'race_day'}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Row", *self.columns])
                for i, row in enumerate(_without_trailing_blank_rows(self._values()), start=1):
                    writer.writerow([i, *row])
        except OSError as exc:
            messagebox.showerror("Export CSV", f"Could not write the file: {exc.strerror or exc}",
                                 parent=self)
            return
        messagebox.showinfo("Export CSV", f"Saved to {path}", parent=self)

    def _export_html(self) -> None:
        day = self._race_day("Export HTML")
        if day is None:
            return
        if self._mark_problems() and not messagebox.askyesno(
                "Export HTML", "Some sail numbers are marked as wrong. Export anyway?", parent=self):
            return
        try:
            path = export_race_day_html(
                self.html_folder, day, club_title=self.club_title,
                competition_title=self.competition_title,
                members=self.members, classes=self.classes, clubs=self.clubs)
        except StorageError as exc:
            messagebox.showerror("Export HTML", str(exc), parent=self)
            return
        if messagebox.askyesno("Export HTML", f"Saved to\n{path}\n\nOpen it in your web browser?",
                               parent=self):
            open_in_browser(path)

    # -- showing it -------------------------------------------------------------------------

    def show(self) -> RaceDay | None:
        """Show the window and wait until it is closed. Returns the saved race day, or None."""
        self.geometry(f"+{self._parent.winfo_rootx() + 40}+{self._parent.winfo_rooty() + 40}")
        self.wait_visibility()           # grab_set fails if the window is not on screen yet
        self.grab_set()
        self._mark_problems()
        self._focus_cell(0, 0)
        self.wait_window(self)
        return self.result
