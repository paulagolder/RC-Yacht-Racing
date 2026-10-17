#!/usr/bin/env python3
"""Start the program:

    python main.py                   (lists the competitions in ~/.pyraceresults)
    python main.py --version         (prints the version and its date)
"""

from __future__ import annotations

import argparse
import datetime

from app import __version__, __version_date__

PROGRAM = "pyraceresults"


def version_text() -> str:
    """'pyraceresults 1.01 (17 October 2026)'."""
    date = datetime.date.fromisoformat(__version_date__)
    return f"{PROGRAM} {__version__} ({date.day} {date:%B %Y})"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog=PROGRAM,
                                     description="Enter and edit RC yacht race results.")
    parser.add_argument("-V", "--version", action="version", version=version_text())
    parser.parse_args(argv)

    from app.ui.front_window import FrontWindow     # only once a window is wanted
    FrontWindow().mainloop()


if __name__ == "__main__":
    main()
