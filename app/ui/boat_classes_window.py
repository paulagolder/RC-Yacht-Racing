"""boat_classes_window.py - the window for editing the club's boat classes (yachtclasses.xml).

    BoatClassesWindow(parent, data_dir).show()

Pick a class in the list to change or delete it, or fill in the boxes and click Add.
Nothing is written until Save is clicked; closing with unsaved changes asks first.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from ..model.boat_class import BoatClass, BoatClassList
from ..storage.boat_class_store import BOAT_CLASSES_FILE, load_boat_classes, save_boat_classes
from ..storage.errors import StorageError

COLUMNS = [("key", "Key", 100), ("fullname", "Full name", 140), ("cypher", "Cypher", 80),
           ("symbol", "Symbol", 70)]


class BoatClassesWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk | tk.Toplevel, data_dir):
        super().__init__(parent)
        self._parent = parent
        self.data_dir = Path(data_dir)
        self.title("Boat classes")
        self.transient(parent)
        self.minsize(460, 340)

        self.boat_classes = BoatClassList()
        self._saved: list[BoatClass] = []       # the classes as last saved, to spot changes

        # The list (each row's id is the class's index in self.boat_classes.classes)
        list_frame = ttk.Frame(self, padding=(12, 12, 12, 4))
        list_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(list_frame, columns=[c[0] for c in COLUMNS], show="headings",
                                 selectmode="browse", height=10)
        for column_id, heading, width in COLUMNS:
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._selection_changed())

        # The boxes for one class
        form = ttk.LabelFrame(self, text="Boat class", padding=8)
        form.pack(fill="x", padx=12, pady=4)
        self.key_var, self.fullname_var = tk.StringVar(), tk.StringVar()
        self.cypher_var, self.symbol_var = tk.StringVar(), tk.StringVar()
        ttk.Label(form, text="Key:").grid(row=0, column=0, sticky="w")
        self.key_entry = ttk.Entry(form, textvariable=self.key_var, width=12)
        self.key_entry.grid(row=0, column=1, sticky="w", padx=(4, 12), pady=2)
        ttk.Label(form, text="Full name:").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.fullname_var, width=16).grid(row=0, column=3, sticky="w",
                                                                       padx=(4, 12), pady=2)
        ttk.Label(form, text="Cypher:").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.cypher_var, width=8).grid(row=1, column=1, sticky="w",
                                                                    padx=(4, 12), pady=2)
        ttk.Label(form, text="Symbol:").grid(row=1, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.symbol_var, width=4).grid(row=1, column=3, sticky="w",
                                                                    padx=(4, 12), pady=2)

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=4, pady=(8, 0), sticky="w")
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

    def _refresh(self, select: int | None = None) -> None:
        """Redraw the list. select is an index in boat_classes.classes; the nearest is picked."""
        self.tree.delete(*self.tree.get_children())
        classes = self.boat_classes.classes
        for i, c in enumerate(classes):
            self.tree.insert("", "end", iid=str(i), values=(c.key, c.fullname, c.cypher, c.symbol))
        if select is not None and classes:
            target = str(min(select, len(classes) - 1))
            self.tree.selection_set(target)
            self.tree.see(target)
        self._selection_changed()

    def _selection_changed(self) -> None:
        index = self._selected_index()
        for button in (self.update_button, self.delete_button):
            button.state(["!disabled" if index is not None else "disabled"])
        if index is not None:
            c = self.boat_classes.classes[index]
            self.key_var.set(c.key)
            self.fullname_var.set(c.fullname)
            self.cypher_var.set(c.cypher)
            self.symbol_var.set(c.symbol)
        unsaved = " (not saved yet)" if self._unsaved() else ""
        total = len(self.boat_classes)
        self.status_var.set(f"{total} class{'es' if total != 1 else ''}{unsaved}")

    def _clear_form(self) -> None:
        self.tree.selection_remove(*self.tree.selection())
        for var in (self.key_var, self.fullname_var, self.cypher_var, self.symbol_var):
            var.set("")
        self.key_entry.focus_set()

    # -- changes ----------------------------------------------------------------------------

    def _form_class(self) -> BoatClass:
        return BoatClass(self.key_var.get().strip(), self.fullname_var.get().strip(),
                         self.cypher_var.get().strip(), self.symbol_var.get().strip())

    def _unsaved(self) -> bool:
        return self.boat_classes.classes != self._saved

    def add(self) -> None:
        try:
            self.boat_classes.add(self._form_class())
        except ValueError as exc:
            messagebox.showwarning("Boat classes", str(exc), parent=self)
            return
        self._refresh()
        self._clear_form()          # ready for the next one
        self._selection_changed()

    def update_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        try:
            self.boat_classes.replace(index, self._form_class())
        except ValueError as exc:
            messagebox.showwarning("Boat classes", str(exc), parent=self)
            return
        self._refresh(select=index)

    def delete_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        c = self.boat_classes.classes[index]
        if not messagebox.askyesno("Delete boat class", f"Delete the {c.fullname} class?\n\n"
                                   "Sailors and competitions that use it are not changed.",
                                   parent=self):
            return
        self.boat_classes.remove(index)
        self._clear_form()
        self._refresh(select=index)

    def save(self) -> bool:
        try:
            save_boat_classes(self.boat_classes, self.data_dir)
        except StorageError as exc:
            messagebox.showerror("Cannot save", str(exc), parent=self)
            return False
        self._saved = list(self.boat_classes.classes)
        self._selection_changed()
        self.status_var.set(f"{len(self.boat_classes)} classes, saved to {BOAT_CLASSES_FILE}")
        return True

    def _close(self) -> None:
        if self._unsaved():
            answer = messagebox.askyesnocancel("Unsaved changes", "Save the changes to the boat "
                                               "classes before closing?", parent=self)
            if answer is None or (answer and not self.save()):
                return
        self.destroy()

    # -- showing it -------------------------------------------------------------------------

    def show(self) -> bool:
        """Load the file and show the window until it is closed. False if the file can't be read."""
        try:
            self.boat_classes = load_boat_classes(self.data_dir)
        except StorageError as exc:
            self.destroy()
            messagebox.showerror("Boat classes", str(exc), parent=self._parent)
            return False
        self._saved = list(self.boat_classes.classes)
        self._refresh()
        self.geometry(f"+{self._parent.winfo_rootx() + 40}+{self._parent.winfo_rooty() + 40}")
        self.wait_visibility()
        self.grab_set()
        self.key_entry.focus_set()
        self.wait_window(self)
        return True
