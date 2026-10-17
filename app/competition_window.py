"""competition_window.py - the window for one open competition.

    CompetitionWindow(parent, session, settings, on_close=...)

Pick a race day from the list, and enter or edit its results. Every change is saved to the
competition file as soon as the race day window is saved.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .members import MemberList, load_members
from .models import MAX_RACE_DAYS, RaceDay, default_columns
from .race_day_window import RaceDayWindow
from .results import competition_results
from .results_window import ResultsWindow
from .session import CompetitionSession
from .settings import Settings
from .storage import StorageError


class CompetitionWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, session: CompetitionSession, settings: Settings,
                 on_close: Callable[[], None] | None = None):
        super().__init__(parent)
        self.session = session
        self.settings = settings
        self._on_close = on_close
        self.title(f"{settings.title} - {session.competition.title}")
        self.geometry("900x560")
        self.minsize(720, 440)

        self._build_widgets()
        self._refresh(select=0)       # select the first race day, ready to edit
        self.listbox.focus_set()

        self.bind("<Control-w>", lambda e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

    def close(self) -> None:
        self.destroy()
        if self._on_close is not None:
            self._on_close()

    # -- building the window ----------------------------------------------------------------

    def _build_widgets(self) -> None:
        header = ttk.Frame(self, padding=(12, 10, 12, 4))
        header.pack(fill="x")
        ttk.Button(header, text="Close", command=self.close).pack(side="right", padx=(4, 0))
        self.results_button = ttk.Button(header, text="Generate results", command=self.show_results)
        self.results_button.pack(side="right", padx=(4, 0))
        self.title_var = tk.StringVar()
        self.path_var = tk.StringVar()
        ttk.Label(header, textvariable=self.title_var, font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(header, textvariable=self.path_var, foreground="gray40").pack(anchor="w")

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w",
                  padding=(8, 2)).pack(side="bottom", fill="x")

        body = ttk.Frame(self, padding=(12, 4, 12, 8))
        body.pack(fill="both", expand=True)

        # Left: the list of race days
        self.days_frame = ttk.LabelFrame(body, text="Race days", padding=8)
        self.days_frame.pack(side="left", fill="y")
        self.listbox = tk.Listbox(self.days_frame, height=MAX_RACE_DAYS, width=26,
                                  exportselection=False, activestyle="none")
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._selection_changed())
        self.listbox.bind("<Double-Button-1>", self.edit_race_day)
        self.listbox.bind("<Return>", self.edit_race_day)

        buttons = ttk.Frame(self.days_frame)
        buttons.pack(pady=(8, 0))
        self.new_button = ttk.Button(buttons, text="New", width=8, command=self.new_race_day)
        self.edit_button = ttk.Button(buttons, text="Edit", width=8, command=self.edit_race_day)
        self.delete_button = ttk.Button(buttons, text="Delete", width=8, command=self.delete_race_day)
        for button in (self.new_button, self.edit_button, self.delete_button):
            button.pack(side="left", padx=2)

        # Right: a preview of the selected race day's table
        self.preview_frame = ttk.LabelFrame(body, text="Selected race day", padding=8)
        self.preview_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self.preview = ttk.Treeview(self.preview_frame, show="headings", selectmode="none")
        scrollbar = ttk.Scrollbar(self.preview_frame, orient="vertical", command=self.preview.yview)
        self.preview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.preview.pack(side="left", fill="both", expand=True)

    # -- refreshing what is on screen -------------------------------------------------------

    def _selected_index(self) -> int | None:
        selection = self.listbox.curselection()
        return int(selection[0]) if selection else None

    def _refresh(self, select: int | None = None) -> None:
        """Redraw the list, select a race day, and update the preview and buttons."""
        self.listbox.delete(0, tk.END)
        session = self.session
        days = session.competition.race_days
        self.title_var.set(session.competition.title)
        self.path_var.set(str(session.path))
        self.days_frame.configure(text=f"Race days ({len(days)} of {MAX_RACE_DAYS})")
        for day in days:
            self.listbox.insert(tk.END, day.name)
        if days and select is not None:
            index = min(max(select, 0), len(days) - 1)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)
        self._selection_changed()

    def _selection_changed(self) -> None:
        self._show_preview()
        session = self.session
        index = self._selected_index()
        can_add = len(session.competition.race_days) < MAX_RACE_DAYS
        self.new_button.state(["!disabled" if can_add else "disabled"])
        self.results_button.state(["!disabled" if session.competition.race_days else "disabled"])
        for button in (self.edit_button, self.delete_button):
            button.state(["!disabled" if index is not None else "disabled"])
        if not session.competition.race_days:
            self.status_var.set("No race days yet. Click New to add one.")
        elif index is None:
            self.status_var.set("Select a race day, then click Edit (or double-click it).")
        else:
            self.status_var.set("Click Edit (or double-click) to enter or change the results.")

    def _show_preview(self) -> None:
        tree = self.preview
        tree.delete(*tree.get_children())
        index = self._selected_index()
        if index is None:
            tree.configure(columns=())
            self.preview_frame.configure(text="Selected race day")
            return
        day = self.session.competition.race_days[index]
        ids = ["row"] + [f"c{i}" for i in range(len(day.columns))]   # ids, because names can repeat
        tree.configure(columns=ids)
        tree.heading("row", text="Row")
        tree.column("row", width=50, anchor="center", stretch=False)
        for column_id, name in zip(ids[1:], day.columns):
            tree.heading(column_id, text=name)
            tree.column(column_id, width=110, anchor="w")
        for number, row in enumerate(day.rows, start=1):
            tree.insert("", "end", values=[number, *row])
        self.preview_frame.configure(text=day.name)

    # -- race days --------------------------------------------------------------------------

    def new_race_day(self) -> None:
        session = self.session
        competition = session.competition
        if len(competition.race_days) >= MAX_RACE_DAYS:
            messagebox.showinfo("Race days", f"A competition can have at most {MAX_RACE_DAYS} race days.",
                                parent=self)
            return
        members = self._load_members()
        if members is None:
            return
        draft = RaceDay(competition.next_race_day_name(), default_columns(self.settings.default_columns))
        result = RaceDayWindow(self, draft, title=f"{competition.title} - new race day",
                               default_rows=self.settings.default_rows, members=members,
                               boat_class=competition.boat_class,
                               **self._export_options()).show()
        if result is None:
            return
        try:
            index = session.add_race_day(*result)
        except (ValueError, StorageError) as exc:
            messagebox.showerror("Cannot save", str(exc), parent=self)
            return
        self._refresh(select=index)

    def edit_race_day(self, _event: object = None) -> str:
        session, index = self.session, self._selected_index()
        if index is not None:
            members = self._load_members()
            if members is None:
                return "break"
            day = session.competition.race_days[index]
            result = RaceDayWindow(self, day, title=f"{session.competition.title} - {day.name}",
                                   default_rows=self.settings.default_rows, members=members,
                                   boat_class=session.competition.boat_class,
                                   **self._export_options()).show()
            if result is not None:
                try:
                    session.update_race_day(index, *result)
                except (ValueError, StorageError) as exc:
                    messagebox.showerror("Cannot save", str(exc), parent=self)
                self._refresh(select=index)
        return "break"

    def show_results(self) -> None:
        """Open a window with every competitor's races and points over all race days so far."""
        try:
            members = load_members(self.settings.data_dir)
        except StorageError:
            members = None                 # still show the results, just without names
        competition = self.session.competition
        ResultsWindow(self, competition_results(competition, members), competition.title)

    def _export_options(self) -> dict:
        """Where and how the race day window's Export HTML writes: a folder for this competition."""
        return {"html_folder": self.settings.output_dir / self.session.path.stem,
                "competition_title": self.session.competition.title,
                "club_title": self.settings.title}

    def _load_members(self) -> MemberList | None:
        """Read the club's sail numbers afresh, so changes to the file are picked up."""
        try:
            members = load_members(self.settings.data_dir)
        except StorageError as exc:
            messagebox.showerror("Club sailors", str(exc), parent=self)
            return None
        if not members.sailors:
            messagebox.showwarning(
                "Club sailors", "No club sailors are listed yet. Add them with File > Club sailors "
                "in the competitions window before entering sail numbers.", parent=self)
        return members

    def delete_race_day(self) -> None:
        session, index = self.session, self._selected_index()
        if index is None:
            return
        day = session.competition.race_days[index]
        if not messagebox.askyesno("Delete race day",
                                   f"Delete '{day.name}' and all its results?\n\nThis cannot be undone.",
                                   icon="warning", parent=self):
            return
        try:
            session.delete_race_day(index)
        except StorageError as exc:
            messagebox.showerror("Cannot save", str(exc), parent=self)
        self._refresh(select=index)
