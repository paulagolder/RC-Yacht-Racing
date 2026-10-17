"""report_window.py - shows a competition's text summary.

    ReportWindow(parent, text, title, folder=...)

Save writes the text to a file (in folder, to begin with); Copy puts it on the clipboard.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..model.competition import safe_file_name

FONT = ("TkFixedFont", 10)


class ReportWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, text: str, title: str, folder: Path | None = None):
        super().__init__(parent)
        self.text = text
        self.folder = folder
        self._file_name = f"{safe_file_name(title, 'competition')}_report.txt"
        self.title(f"{title} - report")
        self.geometry("640x460")
        self.minsize(400, 260)

        bar = ttk.Frame(self, padding=(12, 0, 12, 12))
        bar.pack(side="bottom", fill="x")
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right", padx=2)
        ttk.Button(bar, text="Save...", command=self.save).pack(side="left", padx=2)
        ttk.Button(bar, text="Copy", command=self.copy).pack(side="left", padx=2)
        self.status_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.status_var, foreground="gray40").pack(side="left", padx=8)

        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        view = tk.Text(body, font=FONT, wrap="none", padx=8, pady=8)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=view.yview)
        view.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        view.pack(side="left", fill="both", expand=True)
        view.insert("1.0", text)
        view.configure(state="disabled")             # a report, not for editing

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def copy(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.text)
        self.status_var.set("Copied to the clipboard.")

    def save(self) -> None:
        initialdir = self.folder if self.folder is not None and self.folder.is_dir() else None
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt", filetypes=[("Text files", "*.txt")],
            initialdir=initialdir, initialfile=self._file_name)
        if not path:
            return
        try:
            Path(path).write_text(self.text, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save report", f"Could not write the file: {exc.strerror or exc}",
                                 parent=self)
            return
        self.status_var.set(f"Saved to {path}")
