"""results_window.py - the results of a competition so far.

    ResultsWindow(parent, results, title)

One row per competitor: their points on each race day, the number of races sailed and their
total points (1st place = 1 point, 2nd = 2, ...). The rows start with the fewest points first;
click a column heading to sort by it.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .results import Results, _sort_key


class ResultsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, results: Results, title: str):
        super().__init__(parent)
        self.results = results
        self.title(f"{title} - results")
        self.geometry("820x480")
        self.minsize(500, 300)

        header = ttk.Frame(self, padding=(12, 10, 12, 4))
        header.pack(fill="x")
        ttk.Button(header, text="Close", command=self.destroy).pack(side="right")
        ttk.Label(header, text=f"{title} results", font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(header, text="Points: 1st place = 1, 2nd = 2 ... (fewer is better). "
                               "Click a heading to sort.", foreground="gray40").pack(anchor="w")

        body = ttk.Frame(self, padding=(12, 4, 12, 12))
        body.pack(fill="both", expand=True)
        day_ids = [f"d{i}" for i in range(len(results.day_names))]   # ids, because names can repeat
        self.tree = ttk.Treeview(body, columns=["sail", "name", *day_ids, "races", "points"],
                                 show="headings", selectmode="browse")
        self.tree.heading("sail", text="Sail number")
        self.tree.column("sail", width=90, anchor="w", stretch=False)
        self.tree.heading("name", text="Name")
        self.tree.column("name", width=160, anchor="w")
        for column_id, name in zip(day_ids, results.day_names):
            self.tree.heading(column_id, text=name)
            self.tree.column(column_id, width=80, anchor="center", stretch=False)
        self.tree.heading("races", text="Races")
        self.tree.column("races", width=60, anchor="center", stretch=False)
        self.tree.heading("points", text="Points")
        self.tree.column("points", width=60, anchor="center", stretch=False)
        for column_id in self.tree["columns"]:
            self.tree.heading(column_id, command=lambda c=column_id: self.sort_by(c))

        yscroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(body, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        xscroll.pack(side="bottom", fill="x")
        yscroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        if not results.competitors:
            self.tree.insert("", "end", values=["", "No results entered yet."])
        for result in results.competitors:
            days = ["" if p is None else p for p in result.day_points]
            self.tree.insert("", "end", values=[result.sail_number, result.name or "(not a club sailor)",
                                                *days, result.races, result.points])
        self._sorted_by: str | None = "points"   # rows start fewest points first, as results gives them

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def sort_by(self, column_id: str) -> None:
        """Sort the rows by one column; clicking the same heading again reverses the order."""
        reverse = self._sorted_by == column_id
        self._sorted_by = None if reverse else column_id

        def key(item: str):
            value = str(self.tree.set(item, column_id))
            if column_id == "sail":
                return _sort_key(value)
            if column_id == "name":
                return (0, 0, value.lower())
            return (1, 0, "") if value == "" else (0, int(value), "")    # not sailed goes last

        items = sorted(self.tree.get_children(), key=key, reverse=reverse)
        for index, item in enumerate(items):
            self.tree.move(item, "", index)
