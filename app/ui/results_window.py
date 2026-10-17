"""results_window.py - the results of a competition so far: the current or final table.

    ResultsWindow(parent, results, title, html_folder=..., club_title=...)

One row per boat (a sail number in a class): its place, its points on each race day, the number
of races sailed and its totals (see services/results_table.py). The current table ranks every
boat by average points per race; the final table only has the boats that have sailed enough
races, ranked by points. Click a column heading to sort by it. Export HTML writes the table as a
web page in html_folder (no folder: no button) and offers to open it in the web browser.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from ..model.results import Results
from ..model.sail_number import sort_key
from ..services.html_export import export_results_html
from ..services.results_table import results_note, total_columns, total_values
from ..storage.errors import StorageError
from .browser import open_in_browser


class ResultsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, results: Results, title: str,
                 html_folder: Path | None = None, club_title: str = ""):
        super().__init__(parent)
        self.results = results
        self.competition_title = title
        self.html_folder = html_folder
        self.club_title = club_title
        self.title(f"{title} - {results.title.lower()}")
        self.geometry("880x480")
        self.minsize(500, 300)

        header = ttk.Frame(self, padding=(12, 10, 12, 4))
        header.pack(fill="x")
        ttk.Button(header, text="Close", command=self.destroy).pack(side="right")
        if html_folder is not None:
            ttk.Button(header, text="Export HTML", command=self.export_html).pack(
                side="right", padx=(0, 4))
        ttk.Label(header, text=f"{title} - {results.title.lower()}",
                  font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(header, text=f"{results_note(results)} Click a heading to sort.",
                  foreground="gray40", wraplength=760, justify="left").pack(anchor="w")

        body = ttk.Frame(self, padding=(12, 4, 12, 12))
        body.pack(fill="both", expand=True)
        day_ids = [f"d{i}" for i in range(len(results.day_names))]   # ids, because names can repeat
        totals = total_columns(results)
        self.tree = ttk.Treeview(body, columns=["place", "sail", "class", "name", *day_ids,
                                                *(c for c, _ in totals)],
                                 show="headings", selectmode="browse")
        for column_id, heading, width, anchor in (("place", "Place", 50, "center"),
                                                  ("sail", "Sail number", 90, "w"),
                                                  ("class", "Class", 80, "w")):
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=width, anchor=anchor, stretch=False)
        self.tree.heading("name", text="Name")
        self.tree.column("name", width=160, anchor="w")
        for column_id, name in zip(day_ids, results.day_names):
            self.tree.heading(column_id, text=name)
            self.tree.column(column_id, width=max(80, 7 * len(name)), anchor="center", stretch=False)
        for column_id, heading in totals:
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=70, anchor="center", stretch=False)
        for column_id in self.tree["columns"]:
            self.tree.heading(column_id, command=lambda c=column_id: self.sort_by(c))

        yscroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(body, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        xscroll.pack(side="bottom", fill="x")
        yscroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        if not results.competitors:
            empty = "No boat has sailed enough races yet." if results.left_out else "No results entered yet."
            self.tree.insert("", "end", values=["", "", "", empty])
        for place, result in zip(results.places(), results.competitors):
            days = ["" if p is None else p for p in result.day_points]
            values = total_values(result)
            self.tree.insert("", "end", values=[place, result.sail_number, result.boat_class,
                                                result.name or "(not a club sailor)", *days,
                                                *(values[c] for c, _ in totals)])
        self._sorted_by: str | None = "place"    # rows start in place order, as results gives them

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def export_html(self) -> None:
        try:
            path = export_results_html(self.html_folder, self.results, club_title=self.club_title,
                                       competition_title=self.competition_title)
        except StorageError as exc:
            messagebox.showerror("Export HTML", str(exc), parent=self)
            return
        if messagebox.askyesno("Export HTML", f"Saved to\n{path}\n\nOpen it in your web browser?",
                               parent=self):
            open_in_browser(path)

    def sort_by(self, column_id: str) -> None:
        """Sort the rows by one column; clicking the same heading again reverses the order."""
        reverse = self._sorted_by == column_id
        self._sorted_by = None if reverse else column_id

        def key(item: str):
            value = str(self.tree.set(item, column_id))
            if column_id == "sail":
                return sort_key(value)
            if column_id in ("class", "name"):
                return (0, 0, value.lower())
            return (1, 0, "") if value == "" else (0, float(value), "")  # not sailed goes last

        items = sorted(self.tree.get_children(), key=key, reverse=reverse)
        for index, item in enumerate(items):
            self.tree.move(item, "", index)
