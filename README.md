# RC Yacht Race Tables

Enter and edit race results for radio-controlled model sailing yachts.

- A **competition** is one boat class plus a year (for example *DF95 2026*) and lives in one XML file.
- A competition holds up to **15 race days**.
- A **race day** is a small table: up to **6 races (columns, Race A, Race B ...) and 15 rows**.
- Each cell is a **sail number**, which must belong to a club sailor in the competition's class.

## The data folder

Everything lives in `~/.pyraceresults` (created on first run):

- `properties.xml`: the window title, the default number of rows and columns for a new race day, and
  `output_folder`, where **Export HTML** writes (default `~/Documents/raceresult_output`).
- `RMBCSail.xml`: the club sailors, one `<sail sailnumber="   01" boatclass="DF95" forename=".." surname=".." club="RMBC" />` per boat. Edit it with the
  **File > Club sailors...** menu in the competitions window, then click Save. "Show class" limits the list to one class.
- Competition files, named like `DF95_2026.cxml`. New competitions are saved here, and every
  `.cxml` file here is listed in the first window. (File > Open other file opens one from elsewhere.)

The first window lists every competition in the data folder. Double-click one (or select it and click
**Open**) to open it in its own window, or click **New competition**. **Rename...** changes its boat class
or year; **Delete** takes it off the list (the file is kept as `.cxml.deleted`, rename it back to restore it). In a competition's window, pick a
race day and click **Edit** (or double-click it). Saving the race day window writes the competition file
straight away.

## Running it

Needs Python 3.9 or newer with tkinter (included with the Windows and macOS installers from python.org;
on Debian/Ubuntu install `python3-tk`). Nothing else to install.

    python main.py                   # lists the competitions in ~/.pyraceresults
    python main.py DF95_2026.cxml    # also opens a competition straight away

## Web pages of the results

In the race day window, **Export HTML** writes the table as a web page, with each sailor's name under
their sail number. It goes in `output_folder` (see properties.xml), in a folder named after the
competition file, for example `~/Documents/raceresult_output/DF95_2026/Race_day_1.html`. Exporting
the same race day again replaces its page. The page is a single file (logo included), ready to email,
upload or print.

## Making a Linux program file

    pipx install pyinstaller         # once
    ./build_linux.sh                 # runs the tests, then builds dist/pyraceresults

`dist/pyraceresults` is a single file with Python included, so it runs on Linux machines without
Python installed. Copy it anywhere (for example `~/.local/bin`) and run it. It works on the Linux
version it was built on and newer ones, so build on the oldest one you need. Replacing it with a new
build never touches anyone's `~/.pyraceresults` data.

In the race day window, **Enter**, **Tab** or **Down** moves down the column (adding a row at the bottom until
there are 15, then moving to the top of the next column); **Shift+Tab** or **Up** goes back.
**Add row / Add column** grow the table, up to the limits.

## Project layout

    main.py                 starts the program
    app/
        models.py           Competition and RaceDay, with all the rules and limits (no GUI)
        storage.py          reads and writes the XML file (no GUI)
        session.py          an open file: every change is saved at once, and undone if saving fails (no GUI)
        table_entry.py      the race day table window
        dialogs.py          the New competition window
        settings.py         the data folder and properties.xml (no GUI)
        members.py          club sailors in RMBCSail.xml, and checking sail numbers (no GUI)
        sailors_window.py   the Club sailors window
        html_export.py      a race day as a web page (no GUI)
        resources/          club_logo.svg (the original) and club_logo.png (made from it by build_linux.sh)
        front_window.py     the first window: the list of competitions
        competition_window.py  one competition: its race days and a preview
    tests/                  python -m unittest discover -s tests -t .

Everything that is not a window is tested without needing a screen. To change a limit (columns, rows,
race days), edit the constants at the top of `app/models.py`.

## The file

    <competition class="DF95" year="2026" version="1">
      <raceday name="Race day 1">
        <columns><column>Race A</column> ...</columns>
        <row><cell>text</cell> ...</row>
      </raceday>
    </competition>

Each save keeps the previous version beside it as `DF95_2026.cxml.bak`.
