# RC Yacht Racing

Enter and edit race results for radio-controlled model sailing yachts.

- A **competition** has a name, a year, one or more boat classes and the clubs whose sailors may race,
  and lives in one XML file. It holds up to **15 race days**.
- A **race day** has a date (typed as day/month/year, today's for a new one) and a name, which by
  default is made from the date ("Race Day 30-12-1978") and follows it until you change it. It is a
  small table: up to **6 races (columns, Race A, Race B ...) and 15 rows**.
- A competition's classes are typed as a list separated by commas ("DF65, Victoria"); each must be
  one of the classes in `yachtclasses.xml`, typed by its key or full name in any case. They are
  stored as class ids without repeats (`classes="df65,victoria"`).
- Every race day is open to all the competition's classes, and shows them but cannot change them.
  Each cell is a **sail number**, which must belong to a sailor in one of those classes from one
  of the competition's clubs (see **Entering sail numbers** below).

## The data folder

Everything lives in `~/.pyraceresults` (created on first run):

- `properties.xml`: the window title, the default number of rows and columns for a new race day, and
  `output_folder`, where **Export HTML** writes (default `~/Documents/raceresult_output`).
- `RMBCSail.xml`: the club sailors, one `<sail sailnumber="   01" boatclass="DF95" forename=".." surname=".." club="RMBC" tag="PG" />` per boat (tag: see below). Edit it with the
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
    python main.py --version         # pyraceresults 1.03 (17 October 2026)
    python main.py --data FOLDER     # uses another data folder

## Entering sail numbers

A race day is open to all the competition's classes, so a sail number may be more than one
eligible sailor's. As each number is typed the window says whose it is:

- **No match**: "Unrecognised sail", and the cell is marked.
- **One match**: that sailor.
- **More than one**: when the cursor leaves the cell (Enter, Tab ...), a list asks which, and the
  number is tagged with your choice: `62*` (a **class tag**, the class's symbol from
  `yachtclasses.xml`) when the choices are one sailor in different classes, or `29/PAG` (a
  **sailor tag**) when they are different sailors. Save also asks for any still to choose.

Each sailor's tag is their initials unless changed in **Club sailors** (Tag). If two sailors with
the same sail number in different classes have the same initials, give one of them another tag,
such as PAG and PGU; the window will not accept a clashing one.

## Results so far

In a competition's window, the **Results** button offers two tables. Each has one row per
competitor: a club sailor, with every sail number they sailed in any of the classes ("440 / 23").
A sailor sails one boat at a time, so their boats are alternatives and all their races count together (the
race day window marks a sailor who appears twice in one race). A sail number that is no club
sailor's is a competitor of its own. Each row has the place, the points on each race day and how
many races were sailed. A finish earns its place in points (row 1 = 1st =
1 point, row 2 = 2 points ...), so fewer is better, and equal scores share a place.

- **Current results**: every sailor, ranked by their average points per race sailed, however many
  races they have sailed. Useful during the season, when not everyone can make every race day.
- **Final results**: only the sailors who have sailed the competition's **races counted**
  (`racecount`) or more, ranked by the points from their best that many races. It needs races
  counted to be set (Edit in the competitions list).

Click a column heading to sort by it; click it again to reverse.

**Report** gives a short text summary: the number of race days, races sailed and finishes, how many
different sailors have taken part (in each class), how many have qualified for the final results,
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

## Security check

`./security_check.sh` checks the code with Bandit (`pipx install bandit`) and writes the report
into the output folder, in `security/`. See [SECURITY.md](SECURITY.md) for what the program does
outside its own files and what the findings mean.

## Making the program files

Each is a single file with Python included, so it runs on computers without Python installed.
Data is not part of the program: replacing it with a new build never touches anyone's
`.pyraceresults` folder.

**Linux** (on Linux):

    pipx install pyinstaller         # once
    ./build_linux.sh                 # runs the tests, then builds dist/pyraceresults

It runs on the Linux version it was built on and newer ones, so build on the oldest one you need.

The build also makes a **portable copy** for a USB stick, `dist/RC-Yacht-Racing/`:

    RC-Yacht-Racing/
        pyraceresults        the program
        output/              exported web pages: the only folder users need to open
        system/              the data folder (instead of ~/.pyraceresults), README.txt and
                             start-linux.sh

To make a stick, plug it in and run

    ./make_stick.sh /media/$USER/STICK         # data from ~/.pyraceresults (or name another)

It builds the program if needed and copies the club's files into `system/` (with
`output_folder` set to `output`). On a stick that already has data it only updates the
program, leaving the data alone. It ends by saying whether the program runs straight from the
stick: Linux only runs `.exe`, `.bat` and `.com` files from FAT32 sticks, so on those use
`start-linux.sh` (below), or format the stick exFAT.

The program uses a `system` folder beside it as its data folder, and there the default
`output_folder` is `output` (a relative output folder is beside the data folder). Copy the whole
folder to the stick and put the club's files (`RMBCSail.xml`, `properties.xml`,
`yachtclasses.xml`, competitions) in `system/`. If a stick will not let the program run,
`bash system/start-linux.sh` runs a temporary copy of it with the stick's data. `--data FOLDER`
picks any data folder by hand.

**Windows** (on Windows, with Python from python.org):

    py -m pip install pyinstaller    # once
    build_windows.bat                # runs the tests, then builds dist\pyraceresults.exe

The .exe is not code-signed, so Windows may warn "Windows protected your PC": click
**More info**, then **Run anyway**.

**Both at once, on GitHub**: push a version tag and GitHub builds both (on Ubuntu 22.04 and
Windows), runs the tests on each, and publishes them as a release to download:

    git tag -a v1.03 -m "pyraceresults 1.03"
    git push origin v1.03

See `.github/workflows/release.yml`. It can also be run by hand from the Actions tab to check
the builds without publishing anything.

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
            member_list.py      MemberList: the club sailors
            sail_entry.py       SailResolver: which sailor an entry ("12", "12@", "29/PAG") means; checks race days
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
            sail_chooser.py     asks which sailor an ambiguous sail number means
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
