"""results_window.py - the results of a competition so far: the current or final table.

    ResultsWindow(parent, results, title, html_folder=..., club_title=...)

One row per competitor (a club sailor in a class, with every sail number they sailed; or a
sail number that is no club sailor's): its place, its heats and points on each race day, the
number of races sailed and its totals (see services/results_table.py). The current table ranks every
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
from ..services.results_table import (day_dates, results_note, total_columns, total_groups,
                                      total_values)
from ..storage.errors import StorageError
from .browser import open_in_browser

SHORT = {"Heats": "Hts", "Points": "Pts"}     # grouped headings, kept narrow on screen


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
        ttk.Label(header, text=" ".join(filter(None, [results_note(results), "Click a heading to sort."])),
                  foreground="gray40", wraplength=760, justify="left").pack(anchor="w")

        body = ttk.Frame(self, padding=(12, 4, 12, 12))
        body.pack(fill="both", expand=True)
        days = range(len(results.day_names))               # ids, because names can repeat
        day_ids = [column for d in days for column in (f"h{d}", f"d{d}")]   # heats, points
        totals = total_columns(results)
        self.tree = ttk.Treeview(body, columns=["place", "sail", "name", *day_ids,
                                                *(c for c, _, _ in totals)],
                                 show="headings", selectmode="browse")
        for column_id, heading, width, anchor in (("place", "Place", 50, "center"),
                                                  ("sail", "Sail numbers", 100, "w")):
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=width, anchor=anchor, stretch=False)
        self.tree.heading("name", text="Name")
        self.tree.column("name", width=160, anchor="w")
        self.groups: dict[str, tuple[str, list[str]]] = {}   # first column -> (heading, columns)
        for d, date in zip(days, day_dates(results)):
            width = max(40, 7 * len(date) // 2)            # the two columns share the date
            self.tree.heading(f"h{d}", text="Hts")
            self.tree.heading(f"d{d}", text="Pts")
            self.tree.column(f"h{d}", width=width, anchor="center", stretch=False)
            self.tree.column(f"d{d}", width=width, anchor="center", stretch=False)
            self.groups[f"h{d}"] = (f"Race\n{date}", [f"h{d}", f"d{d}"])
        for column_id, heading, group in totals:
            self.tree.heading(column_id, text=SHORT.get(heading, heading) if group else heading)
            self.tree.column(column_id, width=45 if group else 70, anchor="center", stretch=False)
        for group, column_ids in total_groups(totals):
            if group:
                self.groups[column_ids[0]] = (group, column_ids)
        for column_id in self.tree["columns"]:
            self.tree.heading(column_id, command=lambda c=column_id: self.sort_by(c))

        # A Treeview heading can't span columns, so "Race / date" over each race day's Heats
        # and Points (and the final table's "All races" and "Best 20") is drawn on a band
        # above, scrolled sideways with the table.
        self.days_band = tk.Canvas(body, height=34, highlightthickness=0, borderwidth=0)
        yscroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.xscroll = ttk.Scrollbar(body, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=self._scrolled_sideways)
        self.days_band.grid(row=0, column=0, sticky="ew")
        self.tree.grid(row=1, column=0, sticky="nsew")
        yscroll.grid(row=1, column=1, sticky="ns")
        self.xscroll.grid(row=2, column=0, sticky="ew")
        body.rowconfigure(1, weight=1)
        body.columnconfigure(0, weight=1)
        # after_idle: once the table has stretched Name to fit, or a column has been resized
        self.tree.bind("<Configure>", lambda e: self.after_idle(self._draw_days_band), add="+")
        self.tree.bind("<ButtonRelease-1>", lambda e: self.after_idle(self._draw_days_band),
                       add="+")

        if not results.competitors:
            empty = "No one has sailed enough races yet." if results.left_out else "No results entered yet."
            self.tree.insert("", "end", values=["", "", empty])
        for place, result in zip(results.places(), results.competitors):
            heats = result.day_races or [""] * len(result.day_points)
            days = [cell for h, p in zip(heats, result.day_points)
                    for cell in (("", "") if p is None else (h, p))]
            values = total_values(result, results.race_count)
            self.tree.insert("", "end", values=[place, result.sail_numbers,
                                                result.name or "(not a club sailor)", *days,
                                                *(values[c] for c, _, _ in totals)])
        self._sorted_by: str | None = "place"    # rows start in place order, as results gives them

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def _scrolled_sideways(self, first: str, last: str) -> None:
        self.xscroll.set(first, last)
        self.days_band.xview_moveto(first)

    def _draw_days_band(self) -> None:
        """Each group's heading ('Race' and the date ...) over its columns, lined up with the
        table."""
        band = self.days_band
        band.delete("all")
        widths = {c: int(self.tree.column(c, "width")) for c in self.tree["columns"]}
        x = 0
        for column_id in self.tree["columns"]:
            if column_id in self.groups:
                heading, column_ids = self.groups[column_id]
                width = sum(widths[c] for c in column_ids)
                band.create_rectangle(x, 0, x + width - 1, 33, outline="gray60", fill="gray88")
                band.create_text(x + width // 2, 17, text=heading,
                                 justify="center", font=("TkDefaultFont", 9, "bold"))
            x += widths[column_id]
        band.configure(scrollregion=(0, 0, max(x, self.tree.winfo_width()), 34))
        band.xview_moveto(self.tree.xview()[0])

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
                return sort_key(value.split(" / ")[0])           # by the first sail number
            if column_id == "name":
                return (0, 0, value.lower())
            return (1, 0, "") if value == "" else (0, float(value), "")  # not sailed goes last

        items = sorted(self.tree.get_children(), key=key, reverse=reverse)
        for index, item in enumerate(items):
            self.tree.move(item, "", index)
