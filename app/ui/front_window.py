"""front_window.py - the first window: every competition in the data folder.

Competition files (*.cxml) in the data folder (~/.pyraceresults, or a portable copy's system
folder) are listed here. Double-click one (or select it
and click Open) to open it in its own window. Edit changes a competition's name, classes, clubs
and so on (and its file name to match the name); New creates a file in the folder. Delete takes it off the list by renaming the file to .cxml.deleted, so it can be brought
back.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from ..services.session import CompetitionSession
from ..storage.competition_store import (
    delete_competition,
    list_competitions,
    load_competition,
    suggested_filename,
    update_competition_details,
)
from ..storage.boat_class_store import boat_classes_or_defaults
from ..storage.errors import StorageError
from ..storage.settings_store import DATA_DIR, LOGO_FILE, load_settings
from .boat_classes_window import BoatClassesWindow
from .competition_window import CompetitionWindow
from .competition_dialog import CompetitionDialog
from .sailors_window import SailorsWindow

COLUMNS = [("competition", "Competition", 220), ("classes", "Boat classes", 130), ("year", "Year", 60),
           ("days", "Race days", 80), ("file", "File", 200)]


class FrontWindow(tk.Tk):
    def __init__(self, data_dir: Path = DATA_DIR):
        super().__init__()
        self.settings = load_settings(data_dir)
        self.title(self.settings.title)
        self.geometry("760x480")
        self.minsize(600, 360)
        self._logo = self._load_logo()
        if self._logo is not None:
            self.iconphoto(True, self._logo)                 # title bar / dock, for every window

        self._paths: list[Path] = []                         # one per row in the list
        self._open: dict[Path, CompetitionWindow] = {}       # so a file is only open once

        self._build_menu()
        self._build_widgets()
        self.refresh()

    # -- building the window ----------------------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New competition...", accelerator="Ctrl+N",
                              command=self.new_competition)
        file_menu.add_command(label="Refresh list", accelerator="F5", command=self.refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Club sailors...", command=self.edit_sailors)
        file_menu.add_command(label="Boat classes...", command=self.edit_boat_classes)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", accelerator="Ctrl+Q", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)
        self.bind("<Control-n>", lambda e: self.new_competition())
        self.bind("<F5>", lambda e: self.refresh())
        self.bind("<Control-q>", lambda e: self.destroy())

    def _build_widgets(self) -> None:
        header = ttk.Frame(self, padding=(12, 10, 12, 4))
        header.pack(fill="x")
        if self._logo is not None:
            ttk.Label(header, image=self._logo).pack(side="left", padx=(0, 12))
        titles = ttk.Frame(header)
        titles.pack(side="left", fill="x", anchor="w")
        ttk.Label(titles, text=self.settings.title, font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(titles, text=f"Competitions in {self.settings.data_dir}",
                  foreground="gray40").pack(anchor="w")

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w",
                  padding=(8, 2)).pack(side="bottom", fill="x")

        buttons = ttk.Frame(self, padding=(12, 0, 12, 8))
        buttons.pack(side="bottom", fill="x")
        self.open_button = ttk.Button(buttons, text="Open", command=self.open_selected)
        self.open_button.pack(side="left", padx=2)
        self.edit_button = ttk.Button(buttons, text="Edit...", command=self.edit_details)
        self.edit_button.pack(side="left", padx=2)
        ttk.Button(buttons, text="New...", command=self.new_competition).pack(side="left", padx=2)
        self.delete_button = ttk.Button(buttons, text="Delete", command=self.delete_selected)
        self.delete_button.pack(side="left", padx=2)
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(side="left", padx=2)
        ttk.Button(buttons, text="Quit", command=self.destroy).pack(side="right", padx=2)

        body = ttk.Frame(self, padding=(12, 4, 12, 8))
        body.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(body, columns=[c[0] for c in COLUMNS], show="headings",
                                 selectmode="browse")
        for column_id, heading, width in COLUMNS:
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._selection_changed())
        self.tree.bind("<Double-Button-1>", lambda e: self.open_selected())
        self.tree.bind("<Return>", lambda e: self.open_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<F2>", lambda e: self.edit_details())

    def _load_logo(self) -> tk.PhotoImage | None:
        try:
            return tk.PhotoImage(master=self, file=LOGO_FILE)
        except tk.TclError:              # missing or unreadable: just go without
            return None

    # -- the list ---------------------------------------------------------------------------

    def refresh(self, select: Path | None = None) -> None:
        """Read the folder again and redraw the list, keeping (or moving to) a selection."""
        if select is None:
            index = self._selected_index()
            select = self._paths[index] if index is not None else None
        self.tree.delete(*self.tree.get_children())
        self._paths = []
        boat_classes = boat_classes_or_defaults(self.settings.data_dir)
        for path, competition, error in list_competitions(self.settings.data_dir):
            if competition is None:
                values = ("(cannot be read)", "", "", "", path.name)
            else:
                classes = boat_classes.display_names(competition.classes)
                values = (competition.title, ", ".join(classes), competition.year,
                          len(competition.race_days), path.name)
            item = self.tree.insert("", "end", values=values)
            self._paths.append(path)
            if select is not None and path.resolve() == select.resolve():
                self.tree.selection_set(item)
                self.tree.see(item)
        if not self._paths:
            self.status_var.set("No competitions yet. Click New to start one.")
        self._selection_changed()

    def _selected_index(self) -> int | None:
        selection = self.tree.selection()
        return self.tree.index(selection[0]) if selection else None

    def _selection_changed(self) -> None:
        index = self._selected_index()
        for button in (self.open_button, self.edit_button, self.delete_button):
            button.state(["!disabled" if index is not None else "disabled"])
        if index is not None:
            self.status_var.set("Click Open (or double-click) to see its race days.")
        elif self._paths:
            count = len(self._paths)
            self.status_var.set(f"{count} competition{'s' if count != 1 else ''}. Select one to open it.")

    # -- opening and creating ---------------------------------------------------------------

    def open_selected(self) -> None:
        index = self._selected_index()
        if index is not None:
            self.open_path(self._paths[index])

    def open_path(self, path: Path) -> None:
        key = path.resolve()
        window = self._open.get(key)
        if window is not None and window.winfo_exists():     # already open: bring it forward
            window.deiconify()
            window.lift()
            window.focus_set()
            return
        try:
            session = CompetitionSession.open(path, boat_classes_or_defaults(self.settings.data_dir))
        except StorageError as exc:
            messagebox.showerror("Cannot open file", str(exc), parent=self)
            return
        self._open[key] = CompetitionWindow(self, session, self.settings,
                                            on_close=lambda: self._closed(key))

    def _closed(self, key: Path) -> None:
        self._open.pop(key, None)
        if self.winfo_exists():
            self.refresh()                # race day counts may have changed

    def new_competition(self) -> None:
        boat_classes = boat_classes_or_defaults(self.settings.data_dir)
        competition = CompetitionDialog(self, boat_classes=boat_classes).show()
        if competition is None:
            return
        path = self.settings.data_dir / suggested_filename(competition)
        if path.exists():
            messagebox.showwarning("New competition", f"There is already a {competition.title} "
                                   f"competition ({path.name}). Open it from the list instead.",
                                   parent=self)
            self.refresh(select=path)
            return
        try:
            CompetitionSession.create(competition, path, boat_classes)
        except StorageError as exc:
            messagebox.showerror("Cannot create file", str(exc), parent=self)
            return
        self.refresh(select=path)
        self.open_path(path)

    # -- changing details and deleting ------------------------------------------------------

    def _is_open(self, path: Path, action: str) -> bool:
        window = self._open.get(path.resolve())
        if window is not None and window.winfo_exists():
            messagebox.showinfo(action, f"{path.name} is open. Close its window first.", parent=self)
            window.lift()
            return True
        return False

    def edit_details(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        path = self._paths[index]
        title = "Competition details"
        if self._is_open(path, title):
            return
        try:
            competition = load_competition(path)
        except StorageError as exc:
            messagebox.showerror(title, str(exc), parent=self)
            return
        details = CompetitionDialog(self, title=title, competition=competition,
                                    boat_classes=boat_classes_or_defaults(self.settings.data_dir)).show()
        if details is None or details.same_details(competition):
            return
        try:
            new_path = update_competition_details(path, details)
        except StorageError as exc:
            messagebox.showerror(title, str(exc), parent=self)
            self.refresh()
            return
        self.refresh(select=new_path)
        self.status_var.set(f"Saved {details.title} ({new_path.name}).")

    def delete_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        path = self._paths[index]
        if self._is_open(path, "Delete competition"):
            return
        values = self.tree.item(self.tree.get_children()[index])["values"]
        name = values[0] if values[1] else path.name         # an unreadable file has no title
        count = values[3]
        days = f" and its {count} race day{'s' if count != 1 else ''}" if count else ""
        if not messagebox.askyesno(
                "Delete competition", f"Delete {name}{days}?\n\nIt will be taken off the "
                f"list. The file is kept as {path.name}.deleted in case you need it back.",
                icon="warning", parent=self):
            return
        try:
            delete_competition(path)
        except StorageError as exc:
            messagebox.showerror("Delete competition", str(exc), parent=self)
            return
        self.refresh()
        self.status_var.set(f"Deleted {path.name} (kept as {path.name}.deleted).")

    def edit_sailors(self) -> None:
        SailorsWindow(self, self.settings.data_dir).show()

    def edit_boat_classes(self) -> None:
        BoatClassesWindow(self, self.settings.data_dir).show()
