# RC Yacht Race Tables

Enter and edit race results for radio-controlled model sailing yachts.

- A **competition** has a name, a year, one or more boat classes and the clubs whose sailors may race,
  and lives in one XML file. It holds up to **15 race days**.
- A **race day** has a name and a date (typed as day/month/year, today's date for a new one) and is a
  small table: up to **6 races (columns, Race A, Race B ...) and 15 rows**.
- A competition's classes are typed as a list separated by commas ("DF65, Victoria"); each must be
  one of the classes in `yachtclasses.xml`, typed by its key or full name in any case. They are
  stored as class ids without repeats (`classes="df65,victoria"`).
- Every race day is open to all the competition's classes, and shows them but cannot change them.
  Each cell is a **sail number**, which must belong to a sailor in one of those classes from one
  of the competition's clubs.

## The data folder

Everything lives in `~/.pyraceresults` (created on first run):

- `properties.xml`: the window title, the default number of rows and columns for a new race day, and
  `output_folder`, where **Export HTML** writes (default `~/Documents/raceresult_output`).
- `RMBCSail.xml`: the club sailors, one `<sail sailnumber="   01" boatclass="DF95" forename=".." surname=".." club="RMBC" />` per boat. Edit it with the
  **File > Club sailors...** menu in the competitions window, then click Save. "Show class" limits the list to one class.
- Competition files, named after the competition, like `Victoria_df65_competition_2026.cxml`.
  New competitions are saved here, and every `.cxml` file here is listed in the first window.
- `yachtclasses.xml`: the boat classes, one `<boatclass key="df95" fullname="DF95" cypher="95" symbol="@" />`
  per class. Edit it with the **File > Boat classes...** menu, then click Save.

The first window lists every competition in the data folder. Double-click one (or select it and click
**Open**) to open it in its own window. **Edit...** changes its name,
year, classes, clubs, races counted or HTML folder (the file is renamed to match the name); **New...**
starts a new competition;
**Delete** takes it off the list (the file is kept as `.cxml.deleted`, rename it back to restore it). In a competition's window, pick a
race day and click **Edit** (or double-click it). Saving the race day window writes the competition file
straight away.

## Running it

Needs Python 3.9 or newer with tkinter (included with the Windows and macOS installers from python.org;
on Debian/Ubuntu install `python3-tk`). Nothing else to install.

    python main.py                   # lists the competitions in ~/.pyraceresults

## Results so far

In a competition's window, the **Results** button offers two tables. Each has one row per boat (a
sail number in a class: the same number in two classes is two boats), with its place, its points on
each race day and how many races it has sailed. A finish earns its place in points (row 1 = 1st =
1 point, row 2 = 2 points ...), so fewer is better, and equal scores share a place.

- **Current results**: every boat, ranked by its average points per race sailed, however many
  races it has sailed. Useful during the season, when not everyone can make every race day.
- **Final results**: only the boats that have sailed the competition's **races counted**
  (`racecount`) or more, ranked by the points from their best that many races. It needs races
  counted to be set (Edit in the competitions list).

Click a column heading to sort by it; click it again to reverse.

**Report** gives a short text summary: the number of race days, races sailed and finishes, how many
different boats have taken part (in each class), how many have qualified for the final results,
each race day's figures and the leading boats in the current results.
**Save...** writes it to a text file and **Copy** puts it on the clipboard.

## Web pages of the results

In the race day window, **Export HTML** writes the table as a web page, with each sailor's name under
their sail number. It goes in `output_folder` (see properties.xml), in the competition's HTML folder
(`directory`), for example `~/Documents/raceresult_output/Victoria2026/Race_day_1.html`. Exporting
the same race day again replaces its page.

In a results window, **Export HTML** writes that table as `results_current.html` or
`results_final.html` in the same folder.

Each page is a single file (logo included), ready to email, upload or print.

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

    main.py                     starts the program
    app/
        model/                  the data classes: no screen, no files
            limits.py           how many races, places and race days; the year range
            boat_class.py       boat classes, and matching them ("DF 95" = "DF95")
            sail_number.py      matching, sorting and writing sail numbers ("1" = "01")
            race.py             Race: its name and finishers in order (place = points)
            race_day.py         RaceDay: a name, a date and its races, also seen as a table
            competition.py      Competition: name, year, classes, clubs, races counted, race days
            sailor.py           Sailor: one club boat
            member_list.py      MemberList: the club sailors, and checking race results against them
            results.py          Results: each competitor's races and points; the current and final tables
            summary.py          CompetitionSummary: the figures for the report
        storage/                reading and writing files
            errors.py           StorageError, with a message that can be shown to the user
            xml_file.py         writes a file safely, keeping a .bak
            competition_store.py  competition (.cxml) files
            member_store.py     the club sailors, RMBCSail.xml
            settings_store.py   Settings: the data folder and properties.xml
        services/               working with the model (no screen)
            session.py          an open file: every change is saved at once, and undone if saving fails
            scoring.py          works out the results over all race days, and the current and final tables
            results_table.py    the columns and scoring note shared by the results window and page
            html_export.py      a race day, or the results, as a web page
            report.py           the text summary of a competition (Report)
        ui/                     the windows
            front_window.py     the first window: the list of competitions
            competition_dialog.py  asks for a competition's details (New and Edit)
            competition_window.py  one competition: its race days and a preview
            race_day_window.py  enter or edit one race day's table
            grid_navigation.py  where Enter/Tab moves to in that table
            results_window.py   the current or final results (Results in a competition's window)
            report_window.py    the text summary (Report in a competition's window)
            browser.py          opens an exported page in the web browser
            sailors_window.py   the Club sailors window
        resources/              club_logo.svg (the original) and club_logo.png (made from it by build_linux.sh)
    tests/                      the same layout as app/: python -m unittest discover -s tests -t .

The layers only call downwards: ui uses services, storage and model; services use storage and
model; storage uses model; model uses nothing else. Everything except ui/ is tested without
needing a screen. To change a limit (races, rows, race days), edit `app/model/limits.py`.

## The file

    <competition year="2026" name="Victoria_df65_competition_2026" racecount="24" clubs="RMBC"
                 directory="Victoria2026" classes="df65,victoria" version="3">
      <raceday name="Race day 1" date="2026-10-10">
        <race name="Race A">
          <sail>12</sail>
          <sail>7</sail>
        </race>
        ...
      </raceday>
    </competition>

A competition holds race days, a race day holds races, and a race holds sail numbers in
finishing order (the first `<sail>` came 1st). An empty `<sail />` is a place left empty.
`classes` and `clubs` are lists separated by commas; `racecount` and `clubs` may be left out
(every race counts; any club). `classes` are the class ids from `yachtclasses.xml`, and every
race day is open to all of them. A race day's `date` is year-month-day and may be left out.

Older files still open and are saved in this layout the next time they change. Versions 1 and 2
have a single `class="DF95"` and no name (the name becomes "DF95 2026"); version 1 stores each race
day as a table of `<columns>` and `<row>`s.

Each save keeps the previous version beside it as `DF95_2026.cxml.bak`.
