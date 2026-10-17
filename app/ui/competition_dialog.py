"""competition_dialog.py - asks for a competition's details.

    details = CompetitionDialog(parent).show()      # a Competition with no race days, or None

Also used to change a competition's details: pass the competition and a window title.
Classes and clubs are typed as lists separated by commas. Left blank, the name is made from
the classes and year, Races counted means every race counts, and the HTML folder is made
from the name.
"""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from ..model.boat_class import BOAT_CLASSES
from ..model.competition import Competition, split_list
from ..model.limits import MAX_YEAR, MIN_YEAR
from ..model.sailor import DEFAULT_CLUB

HINT = {"foreground": "gray40"}


class CompetitionDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, title: str = "New competition",
                 competition: Competition | None = None, class_names: list[str] | None = None):
        super().__init__(parent)
        class_names = class_names or BOAT_CLASSES
        self._title = title
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.result: Competition | None = None
        comp = competition

        frame = ttk.Frame(self, padding=16)
        frame.grid()
        self.name_var = tk.StringVar(value=comp.name if comp else "")
        self.year_var = tk.StringVar(value=str(comp.year if comp else datetime.date.today().year))
        self.classes_var = tk.StringVar(value=", ".join(comp.classes) if comp else class_names[0])
        self.clubs_var = tk.StringVar(value=", ".join(comp.clubs) if comp else DEFAULT_CLUB)
        self.count_var = tk.StringVar(value=str(comp.race_count or "") if comp else "")
        self.directory_var = tk.StringVar(value=comp.directory if comp else "")

        self.name_entry = self._row(frame, 0, "Name:", ttk.Entry(frame, textvariable=self.name_var,
                                                                 width=34), "blank: classes and year")
        self._row(frame, 1, "Year:", ttk.Spinbox(frame, from_=MIN_YEAR, to=MAX_YEAR,
                                                 textvariable=self.year_var, width=8))
        self._row(frame, 2, "Boat classes:", ttk.Combobox(frame, textvariable=self.classes_var,
                                                          values=class_names, width=32),
                  "for example: DF65, Victoria")
        self._row(frame, 3, "Clubs:", ttk.Entry(frame, textvariable=self.clubs_var, width=34),
                  "only their sailors may race; blank: any club")
        self._row(frame, 4, "Races counted:", ttk.Entry(frame, textvariable=self.count_var, width=8),
                  "each boat's best this many races; blank: all")
        self._row(frame, 5, "HTML folder:", ttk.Entry(frame, textvariable=self.directory_var,
                                                      width=34), "for Export HTML; blank: from the name")

        buttons = ttk.Frame(frame)
        buttons.grid(row=12, column=0, columnspan=2, pady=(14, 0))
        ttk.Button(buttons, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())

    def _row(self, frame: ttk.Frame, n: int, label: str, widget: tk.Widget, hint: str = "") -> tk.Widget:
        ttk.Label(frame, text=label).grid(row=2 * n, column=0, sticky="w", pady=(4, 0))
        widget.grid(row=2 * n, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
        if hint:
            ttk.Label(frame, text=hint, **HINT).grid(row=2 * n + 1, column=1, sticky="w", padx=(8, 0))
        return widget

    def _ok(self) -> None:
        try:
            year = int(self.year_var.get().strip())
        except ValueError:
            messagebox.showwarning(self._title, "The year must be a whole number.", parent=self)
            return
        count_text = self.count_var.get().strip()
        try:
            race_count = int(count_text) if count_text else None
        except ValueError:
            messagebox.showwarning(self._title, "Races counted must be a whole number, or blank "
                                   "to count every race.", parent=self)
            return
        classes = split_list(self.classes_var.get())
        name = self.name_var.get().strip() or f"{' '.join(classes)} {year}"
        try:
            self.result = Competition(name, year, classes, split_list(self.clubs_var.get()),
                                      race_count, self.directory_var.get())
        except ValueError as exc:
            messagebox.showwarning(self._title, str(exc), parent=self)
            return
        self.destroy()

    def show(self) -> Competition | None:
        self.wait_visibility()
        self.grab_set()
        self.name_entry.focus_set()
        self.wait_window(self)
        return self.result
