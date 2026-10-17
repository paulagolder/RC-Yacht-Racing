"""competition_store.py - read and write a competition as an XML file.

File layout: a competition holds race days, a race day holds races, and a race holds the
sail numbers of its finishers in finishing order (the first <sail> came 1st):

    <competition year="2026" name="Victoria_df65_competition_2026" racecount="24" clubs="RMBC"
                 directory="Victoria2026" classes="df65,victoria" version="3">
      <raceday name="Race day 1">
        <race name="Race A">
          <sail>12</sail>
          <sail>7</sail>
          ...
        </race>
        ...
      </raceday>
      ...
    </competition>

classes and clubs are lists separated by commas; classes are the class ids (keys) from
yachtclasses.xml. racecount (the best races that count for each boat) and clubs may be left
out, and directory defaults to one made from the name. Every race day is open to all the
competition's classes.

An empty <sail/> is a place left empty; the sails after it keep their places. A new
competition has no race days yet, and a new race has no sails.

Older files can still be read, and are written in this layout the next time they are saved.
Versions 1 and 2 have a single class="DF95" and no name (the name becomes "DF95 2026"); in
version 1 each race day is a table of <columns> and <row>s. A class="..." on a race day,
from before race days were always open to every class, is ignored.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..model.competition import Competition, safe_file_name, split_list
from ..model.race import Race, race_name
from ..model.race_day import RaceDay
from .errors import StorageError
from .xml_file import write_xml

FORMAT_VERSION = "3"
EXTENSION = ".cxml"            # competition files, so they stand out from the other files in the folder
MAX_FILE_BYTES = 10_000_000   # a real competition file is a few KB; refuse anything absurd

# Characters XML cannot hold at all (control characters). Removed on save so the file stays readable.
_INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def _clean(text: str) -> str:
    return _INVALID_XML.sub("", text)


def competition_to_xml(comp: Competition) -> ET.Element:
    attributes = {"year": str(comp.year), "name": comp.name}
    if comp.race_count is not None:
        attributes["racecount"] = str(comp.race_count)
    if comp.clubs:
        attributes["clubs"] = ",".join(comp.clubs)
    attributes.update({"directory": comp.directory, "classes": ",".join(comp.classes),
                       "version": FORMAT_VERSION})
    root = ET.Element("competition", {key: _clean(value) for key, value in attributes.items()})
    for day in comp.race_days:
        day_el = ET.SubElement(root, "raceday", {"name": _clean(day.name)})
        for race in day.races:
            race_el = ET.SubElement(day_el, "race", {"name": _clean(race.name)})
            finishers = list(race.finishers)
            while finishers and not finishers[-1].strip():      # empty places at the end
                finishers.pop()
            for sail_number in finishers:
                ET.SubElement(race_el, "sail").text = _clean(sail_number) or None
    return root


def competition_from_xml(root: ET.Element) -> Competition:
    if root.tag != "competition":
        raise StorageError("This is not a competition file (expected a <competition> element).")
    comp = _competition_details(root)
    for index, day_el in enumerate(root.findall("raceday"), start=1):
        name = day_el.get("name") or comp.next_race_day_name()
        try:
            if day_el.find("columns") is not None:
                day = _race_day_from_table_xml(name, day_el)      # version 1
            else:
                day = _race_day_from_xml(name, day_el, index)
            comp.add_race_day(day)
        except ValueError as exc:
            raise StorageError(f"Race day {index}: {exc}") from exc
    return comp


def _competition_details(root: ET.Element) -> Competition:
    year_text = root.get("year")
    if year_text is None:
        raise StorageError("The competition is missing its year.")
    try:
        year = int(year_text)
    except ValueError:
        raise StorageError(f"The year '{year_text}' is not a whole number.") from None

    old_class = root.get("class")                    # versions 1 and 2
    if old_class is not None:
        name, classes = f"{old_class.strip()} {year}", [old_class]
    else:
        name, classes = root.get("name"), split_list(root.get("classes", ""))
        if not name or not classes:
            raise StorageError("The competition is missing its name or classes.")

    count_text = (root.get("racecount") or "").strip()
    try:
        race_count = int(count_text) if count_text else None
    except ValueError:
        raise StorageError(f"The race count '{count_text}' is not a whole number.") from None

    try:
        return Competition(name, year, classes, split_list(root.get("clubs", "")), race_count,
                           root.get("directory", ""))
    except ValueError as exc:
        raise StorageError(str(exc)) from exc


def _race_day_from_xml(name: str, day_el: ET.Element, index: int) -> RaceDay:
    race_els = day_el.findall("race")
    if not race_els:
        raise StorageError(f"Race day {index} has no <race> elements.")
    races = [Race(race_el.get("name") or race_name(n),
                  [(sail_el.text or "") for sail_el in race_el.findall("sail")])
             for n, race_el in enumerate(race_els, start=1)]
    return RaceDay(name, races)


def _race_day_from_table_xml(name: str, day_el: ET.Element) -> RaceDay:
    """A version 1 race day: a table with one column per race and one row per place."""
    columns = [(c.text or "") for c in day_el.find("columns").findall("column")]
    rows = [[(c.text or "") for c in row_el.findall("cell")] for row_el in day_el.findall("row")]
    return RaceDay.from_table(name, columns, rows)


def save_competition(comp: Competition, path) -> None:
    """Write the competition to path, keeping the previous version as '<name>.bak'.

    A failure part-way through cannot leave a half-written competition file. Raises StorageError.
    """
    write_xml(competition_to_xml(comp), Path(path))


def load_competition(path) -> Competition:
    path = Path(path)
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise StorageError(f"{path.name} is too large to be a competition file.")
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise StorageError(f"{path.name} is not valid XML: {exc}") from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path.name}: {exc.strerror or exc}") from exc
    return competition_from_xml(tree.getroot())


def suggested_filename(comp: Competition) -> str:
    return f"{safe_file_name(comp.name, 'competition')}{EXTENSION}"


def list_competitions(folder) -> list[tuple[Path, Competition | None, str]]:
    """Every competition file in folder, as (path, competition, error).

    A file that cannot be read is still listed, with competition None and the reason in error.
    Sorted newest year first, then by name; unreadable files come last.
    """
    found = []
    for path in sorted(Path(folder).glob(f"*{EXTENSION}")):
        try:
            found.append((path, load_competition(path), ""))
        except StorageError as exc:
            found.append((path, None, str(exc)))
    return sorted(found, key=lambda f: (f[1] is None, -(f[1].year if f[1] else 0),
                                        (f[1].name.upper() if f[1] else f[0].name)))


def update_competition_details(path, details: Competition) -> Path:
    """Change a competition's name, year, classes, clubs, race count and directory (keeping its
    race days), and rename its file to match the name.

    Returns the new path. Refuses (StorageError) if another competition already has that
    file name. The backup (.bak) moves with the file.
    """
    path = Path(path)
    comp = load_competition(path)
    try:
        renamed = comp.with_details(details)
    except ValueError as exc:
        raise StorageError(str(exc)) from exc
    new_path = path.with_name(suggested_filename(renamed))
    same_file = new_path.exists() and new_path.samefile(path)   # e.g. only the case changed on Windows
    if new_path.exists() and not same_file:
        raise StorageError(f"There is already a {renamed.title} competition ({new_path.name}).")
    if same_file:
        save_competition(renamed, path)
        if new_path.name != path.name:
            _move(path, new_path)
        return new_path
    save_competition(renamed, new_path)
    _move(path.with_name(path.name + ".bak"), new_path.with_name(new_path.name + ".bak"))
    try:
        path.unlink()
    except OSError as exc:
        raise StorageError(f"Saved as {new_path.name}, but could not remove {path.name}: "
                           f"{exc.strerror or exc}") from exc
    return new_path


def delete_competition(path) -> Path:
    """Take a competition out of the list by renaming it to '<name>.deleted'.

    Nothing is lost: rename the file back to bring it back. Returns the new path.
    """
    path = Path(path)
    deleted = path.with_name(path.name + ".deleted")
    _move(path, deleted)
    return deleted


def _move(source: Path, target: Path) -> None:
    if not source.exists():
        return
    try:
        os.replace(source, target)
    except OSError as exc:
        raise StorageError(f"Could not rename {source.name}: {exc.strerror or exc}") from exc
