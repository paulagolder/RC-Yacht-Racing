"""sail_chooser.py - asks which sailor an ambiguous sail number means.

    entry = SailChooser(parent, "12", [("12/PAG", "Paul Golder (DF95, RMBC)"), ...]).show()

Returns the tagged entry chosen ("12/PAG"), or None if cancelled. A choice whose entry is ""
cannot be tagged (its class has no symbol) and is shown but cannot be picked.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class SailChooser(tk.Toplevel):
    def __init__(self, parent: tk.Misc, value: str, choices: list[tuple[str, str]]):
        super().__init__(parent)
        self._parent = parent
        self.choices = choices
        self.result: str | None = None
        self.title("Which sailor?")
        self.resizable(False, False)
        self.transient(parent)

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=f"Sail '{value}' could be more than one sailor. Choose which:").pack(
            anchor="w")
        width = max(len(entry) for entry, _ in choices) + 2
        self.listbox = tk.Listbox(frame, height=len(choices), width=60, activestyle="none",
                                  exportselection=False, font=("TkFixedFont", 10))
        for entry, description in choices:
            self.listbox.insert(tk.END, f"{entry or '(no tag)':<{width}}{description}")
        self.listbox.pack(fill="both", expand=True, pady=8)
        self.listbox.selection_set(0)
        self.listbox.activate(0)
        if any(not entry for entry, _ in choices):
            ttk.Label(frame, text="(no tag): give the classes symbols in File > Boat classes.",
                      foreground="gray40").pack(anchor="w")

        buttons = ttk.Frame(frame)
        buttons.pack(pady=(4, 0))
        ttk.Button(buttons, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)

        self.listbox.bind("<Double-Button-1>", lambda e: self._ok())
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<KP_Enter>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        for n in range(1, min(len(choices), 9) + 1):           # 1, 2 ... picks a choice
            self.bind(str(n), lambda e, i=n - 1: self._pick(i))

    def _pick(self, index: int) -> None:
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self._ok()

    def _ok(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        entry = self.choices[selection[0]][0]
        if not entry:
            self.bell()
            return
        self.result = entry
        self.destroy()

    def show(self) -> str | None:
        self.geometry(f"+{self._parent.winfo_rootx() + 60}+{self._parent.winfo_rooty() + 60}")
        self.wait_visibility()
        self.grab_set()
        self.listbox.focus_set()
        self.wait_window(self)
        return self.result
