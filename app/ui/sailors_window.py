"""sailors_window.py - the window for editing the club's sailors (RMBCSail.xml).

    SailorsWindow(parent, data_dir).show()

Pick a sailor in the list to change or delete them, or fill in the boxes and click Add.
Tag is a short code (initials, if left blank) that tells sailors apart when two of them have the
same sail number in different classes; change it (for example PG -> PAG) if two such sailors'
initials are the same.
"Show class" limits the list to one boat class.
Nothing is written until Save is clicked; closing with unsaved changes asks first.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from ..model.member_list import MemberList
from ..model.sail_number import format_sail_number
from ..model.sailor import DEFAULT_CLUB, Sailor
from ..storage.boat_class_store import boat_classes_or_defaults
from ..storage.errors import StorageError
from ..storage.member_store import MEMBERS_FILE, load_members, save_members

ALL_CLASSES = "All classes"
COLUMNS = [("sail", "Sail number", 90), ("class", "Boat class", 100), ("forename", "Forename", 120),
           ("surname", "Surname", 130), ("club", "Club", 80), ("tag", "Tag", 50)]


class SailorsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, data_dir):
        super().__init__(parent)
        self._parent = parent
        self.data_dir = Path(data_dir)
        self.title("Club sailors")
        self.transient(parent)
        self.minsize(600, 380)

        self.members = MemberList()
        self._class_names = boat_classes_or_defaults(self.data_dir).names()   # yachtclasses.xml
        self._saved: list[Sailor] = []          # the sailors as last saved, to spot changes

        # The class filter
        filter_bar = ttk.Frame(self, padding=(12, 12, 12, 0))
        filter_bar.pack(fill="x")
        ttk.Label(filter_bar, text="Show class:").pack(side="left")
        self.filter_var = tk.StringVar(value=ALL_CLASSES)
        self.filter_box = ttk.Combobox(filter_bar, textvariable=self.filter_var, state="readonly",
                                       width=16)
        self.filter_box.pack(side="left", padx=6)
        self.filter_box.bind("<<ComboboxSelected>>", lambda e: self._filter_changed())

        # The list (each row's id is the sailor's index in self.members.sailors)
        list_frame = ttk.Frame(self, padding=(12, 6, 12, 4))
        list_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(list_frame, columns=[c[0] for c in COLUMNS], show="headings",
                                 selectmode="browse", height=14)
        for column_id, heading, width in COLUMNS:
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._selection_changed())

        # The boxes for one sailor
        form = ttk.LabelFrame(self, text="Sailor", padding=8)
        form.pack(fill="x", padx=12, pady=4)
        self.sail_var, self.class_var = tk.StringVar(), tk.StringVar()
        self.forename_var, self.surname_var = tk.StringVar(), tk.StringVar()
        self.club_var = tk.StringVar(value=DEFAULT_CLUB)
        self.tag_var = tk.StringVar()
        ttk.Label(form, text="Sail number:").grid(row=0, column=0, sticky="w")
        self.sail_entry = ttk.Entry(form, textvariable=self.sail_var, width=8)
        self.sail_entry.grid(row=0, column=1, sticky="w", padx=(4, 12), pady=2)
        ttk.Label(form, text="Boat class:").grid(row=0, column=2, sticky="w")
        self.class_box = ttk.Combobox(form, textvariable=self.class_var, width=12)
        self.class_box.grid(row=0, column=3, sticky="w", padx=(4, 12), pady=2)
        ttk.Label(form, text="Club:").grid(row=0, column=4, sticky="w")
        ttk.Entry(form, textvariable=self.club_var, width=10).grid(row=0, column=5, sticky="w",
                                                                   padx=4, pady=2)
        ttk.Label(form, text="Forename:").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.forename_var, width=16).grid(row=1, column=1, sticky="w",
                                                                       padx=(4, 12), pady=2)
        ttk.Label(form, text="Surname:").grid(row=1, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.surname_var, width=16).grid(row=1, column=3, sticky="w",
                                                                      padx=(4, 12), pady=2)
        ttk.Label(form, text="Tag:").grid(row=1, column=4, sticky="w")
        ttk.Entry(form, textvariable=self.tag_var, width=6).grid(row=1, column=5, sticky="w",
                                                                 padx=4, pady=2)
        ttk.Label(form, text="blank: initials", foreground="gray40").grid(row=1, column=6, sticky="w")

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=6, pady=(8, 0), sticky="w")
        ttk.Button(buttons, text="Add", command=self.add).pack(side="left", padx=2)
        self.update_button = ttk.Button(buttons, text="Update", command=self.update_selected)
        self.update_button.pack(side="left", padx=2)
        self.delete_button = ttk.Button(buttons, text="Delete", command=self.delete_selected)
        self.delete_button.pack(side="left", padx=2)
        ttk.Button(buttons, text="Clear boxes", command=self._clear_form).pack(side="left", padx=2)

        # Save / close
        bar = ttk.Frame(self, padding=(12, 4, 12, 12))
        bar.pack(fill="x")
        self.status_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.status_var, foreground="gray40").pack(side="left")
        ttk.Button(bar, text="Close", command=self._close).pack(side="right", padx=2)
        ttk.Button(bar, text="Save", command=self.save).pack(side="right", padx=2)

        self.bind("<Escape>", lambda e: self._close())
        self.bind("<Control-s>", lambda e: self.save())
        self.protocol("WM_DELETE_WINDOW", self._close)

    # -- the list ---------------------------------------------------------------------------

    def _selected_index(self) -> int | None:
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def _filter_class(self) -> str | None:
        """The class being shown, or None for all of them."""
        value = self.filter_var.get()
        return None if value == ALL_CLASSES else value

    def _shown(self, sailor: Sailor) -> bool:
        wanted = self._filter_class()
        return wanted is None or sailor.boat_class.strip().upper() == wanted.upper()

    def _show_class_of(self, sailor: Sailor) -> None:
        """Make sure a sailor that was just added or changed is not hidden by the filter."""
        if not self._shown(sailor):
            self.filter_var.set(sailor.boat_class)

    def _filter_changed(self) -> None:
        self._refresh()
        wanted = self._filter_class()
        if wanted:
            self.class_var.set(wanted)      # a new sailor will most likely be in this class
        self.tree.focus_set()

    def _refresh(self, select: int | None = None) -> None:
        """Redraw the list. select is an index in members.sailors; the nearest shown sailor is picked."""
        file_classes = self.members.boat_classes()
        if self._filter_class() not in [None, *file_classes]:
            self.filter_var.set(ALL_CLASSES)    # its last sailor has gone
        self.filter_box.configure(values=[ALL_CLASSES, *file_classes])
        self.class_box.configure(values=list(dict.fromkeys(file_classes + self._class_names)))

        self.tree.delete(*self.tree.get_children())
        shown = [i for i, sailor in enumerate(self.members.sailors) if self._shown(sailor)]
        for i in shown:
            sailor = self.members.sailors[i]
            self.tree.insert("", "end", iid=str(i), values=(
                sailor.number, sailor.boat_class, sailor.forename, sailor.surname, sailor.club,
                sailor.tag))
        if select is not None and shown:
            target = next((i for i in shown if i >= select), shown[-1])
            self.tree.selection_set(str(target))
            self.tree.see(str(target))
        self._selection_changed()

    def _selection_changed(self) -> None:
        index = self._selected_index()
        for button in (self.update_button, self.delete_button):
            button.state(["!disabled" if index is not None else "disabled"])
        if index is not None:
            sailor = self.members.sailors[index]
            self.sail_var.set(sailor.number)
            self.class_var.set(sailor.boat_class)
            self.forename_var.set(sailor.forename)
            self.surname_var.set(sailor.surname)
            self.club_var.set(sailor.club)
            self.tag_var.set(sailor.tag)
        unsaved = " (not saved yet)" if self._unsaved() else ""
        total = len(self.members)
        wanted = self._filter_class()
        if wanted:
            shown = len(self.tree.get_children())
            self.status_var.set(f"Showing {shown} of {total} sails ({wanted}){unsaved}")
        else:
            self.status_var.set(f"{total} sail{'s' if total != 1 else ''}{unsaved}")

    def _clear_form(self) -> None:
        self.tree.selection_remove(*self.tree.selection())
        for var in (self.sail_var, self.forename_var, self.surname_var, self.tag_var):  # class, club stay
            var.set("")
        self.sail_entry.focus_set()

    # -- changes ----------------------------------------------------------------------------

    def _form_sailor(self) -> Sailor:
        sail = self.sail_var.get().strip()
        return Sailor(format_sail_number(sail) if sail else "", self.class_var.get().strip(),
                      self.forename_var.get().strip(), self.surname_var.get().strip(),
                      self.club_var.get().strip(), self.tag_var.get())

    def _unsaved(self) -> bool:
        return self.members.sailors != self._saved

    def add(self) -> None:
        sailor = self._form_sailor()
        try:
            self.members.add(sailor)
        except ValueError as exc:
            messagebox.showwarning("Club sailors", str(exc), parent=self)
            return
        self._show_class_of(sailor)
        self._refresh()
        self._clear_form()          # ready for the next one
        self._selection_changed()

    def update_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        sailor = self._form_sailor()
        try:
            self.members.replace(index, sailor)
        except ValueError as exc:
            messagebox.showwarning("Club sailors", str(exc), parent=self)
            return
        self._show_class_of(sailor)
        self._refresh(select=index)

    def delete_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        sailor = self.members.sailors[index]
        if not messagebox.askyesno("Delete sailor", f"Delete {sailor.name} "
                                   f"({sailor.boat_class} {sailor.number})?", parent=self):
            return
        self.members.remove(index)
        self._clear_form()
        self._refresh(select=index)

    def save(self) -> bool:
        try:
            save_members(self.members, self.data_dir)
        except StorageError as exc:
            messagebox.showerror("Cannot save", str(exc), parent=self)
            return False
        self._saved = list(self.members.sailors)
        self._selection_changed()
        self.status_var.set(f"{len(self.members)} sailors, saved to {MEMBERS_FILE}")
        return True

    def _close(self) -> None:
        if self._unsaved():
            answer = messagebox.askyesnocancel("Unsaved changes", "Save the changes to the club "
                                               "sailors before closing?", parent=self)
            if answer is None or (answer and not self.save()):
                return
        self.destroy()

    # -- showing it -------------------------------------------------------------------------

    def show(self) -> bool:
        """Load the file and show the window until it is closed. False if the file can't be read."""
        try:
            self.members = load_members(self.data_dir)
        except StorageError as exc:
            self.destroy()
            messagebox.showerror("Club sailors", str(exc), parent=self._parent)
            return False
        self._saved = list(self.members.sailors)
        self._refresh()
        self.geometry(f"+{self._parent.winfo_rootx() + 40}+{self._parent.winfo_rooty() + 40}")
        self.wait_visibility()
        self.grab_set()
        self.sail_entry.focus_set()
        self.wait_window(self)
        return True
