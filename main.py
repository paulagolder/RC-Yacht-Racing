#!/usr/bin/env python3
"""Start the program:

    python main.py                   (lists the competitions in ~/.pyraceresults)
    python main.py DF95_2026.cxml    (also opens this competition file straight away)
"""

import sys

from app.front_window import FrontWindow


def main(argv: list[str]) -> None:
    path = argv[1] if len(argv) > 1 else None
    FrontWindow(path).mainloop()


if __name__ == "__main__":
    main(sys.argv)
