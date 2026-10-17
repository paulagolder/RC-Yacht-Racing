#!/usr/bin/env python3
"""Start the program:

    python main.py                   (lists the competitions in ~/.pyraceresults)
    python main.py --version         (prints the version and its date)

The Windows program file has no console (it is built --windowed), so there --version and --help
show their text in a message box instead of printing it.
"""

from __future__ import annotations

import argparse
import datetime
import sys

from app import __version__, __version_date__

PROGRAM = "pyraceresults"


def version_text() -> str:
    """'pyraceresults 1.01 (17 October 2026)'."""
    date = datetime.date.fromisoformat(__version_date__)
    return f"{PROGRAM} {__version__} ({date.day} {date:%B %Y})"


def _show(text: str) -> None:
    """Print text, or show it in a message box when there is no console to print to."""
    if sys.stdout is not None:
        print(text)
        return
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(PROGRAM, text, parent=root)
    root.destroy()


class _Parser(argparse.ArgumentParser):
    def _print_message(self, message: str, file=None) -> None:
        if message:
            _show(message.rstrip("\n"))


class _VersionAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, help="show the version and its date, and exit")

    def __call__(self, parser, namespace, values, option_string=None):
        _show(version_text())
        parser.exit()


def main(argv: list[str] | None = None) -> None:
    parser = _Parser(prog=PROGRAM, description="Enter and edit RC yacht race results.")
    parser.add_argument("-V", "--version", action=_VersionAction)
    parser.parse_args(argv)

    from app.ui.front_window import FrontWindow     # only once a window is wanted
    FrontWindow().mainloop()


if __name__ == "__main__":
    main()
