#!/usr/bin/env python3
"""Start the program:

    python main.py                   (lists the competitions in ~/.pyraceresults)
"""

from app.ui.front_window import FrontWindow


def main() -> None:
    FrontWindow().mainloop()


if __name__ == "__main__":
    main()
