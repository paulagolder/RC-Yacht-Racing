"""new_competition_dialog.py - asks for a boat class and year."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from ..model.boat_class import BOAT_CLASSES
from ..model.competition import Competition
from ..model.limits import MAX_YEAR, MIN_YEAR


class NewCompetitionDialog(tk.Toplevel):
    """Ask for the boat class and year. show() returns an empty Competition, or None if cancelled.

    Also used to rename a competition: pass its current class and year, and a window title.
    """

    def __init__(self, parent: tk.Tk | tk.Toplevel, title: str = "New competition",
                 boat_class: str | None = None, year: int | None = None):
        super().__init__(parent)
        self._title = title
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.result: Competition | None = None

        frame = ttk.Frame(self, padding=16)
        frame.grid()
        ttk.Label(frame, text="Boat class:").grid(row=0, column=0, sticky="w", pady=4)
        self.class_var = tk.StringVar(value=boat_class or BOAT_CLASSES[0])
        self.class_box = ttk.Combobox(frame, textvariable=self.class_var, values=BOAT_CLASSES, width=18)
        self.class_box.grid(row=0, column=1, padx=(8, 0), pady=4)

        ttk.Label(frame, text="Year:").grid(row=1, column=0, sticky="w", pady=4)
        self.year_var = tk.StringVar(value=str(year or datetime.date.today().year))
        ttk.Spinbox(frame, from_=MIN_YEAR, to=MAX_YEAR, textvariable=self.year_var,
                    width=8).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, pady=(14, 0))
        ttk.Button(buttons, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())

    def _ok(self) -> None:
        try:
            year = int(self.year_var.get().strip())
        except ValueError:
            messagebox.showwarning(self._title, "The year must be a whole number.", parent=self)
            return
        try:
            self.result = Competition(self.class_var.get(), year)
        except ValueError as exc:
            messagebox.showwarning(self._title, str(exc), parent=self)
            return
        self.destroy()

    def show(self) -> Competition | None:
        self.wait_visibility()
        self.grab_set()
        self.class_box.focus_set()
        self.wait_window(self)
        return self.result
