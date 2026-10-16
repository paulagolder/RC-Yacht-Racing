"""storage.py - read and write a competition as an XML file. No GUI code here.

File layout:

    <competition class="DF95" year="2026" version="1">
      <raceday name="Race day 1">
        <columns>
          <column>Column A</column>
          ...
        </columns>
        <row>
          <cell>text</cell>
          ...
        </row>
      </raceday>
      ...
    </competition>
"""

from __future__ import annotations

import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import Competition

FORMAT_VERSION = "1"
EXTENSION = ".cxml"            # competition files, so they stand out from the other files in the folder
MAX_FILE_BYTES = 10_000_000   # a real competition file is a few KB; refuse anything absurd

# Characters XML cannot hold at all (control characters). Removed on save so the file stays readable.
_INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


class StorageError(Exception):
    """A competition file could not be read or written. The message is safe to show the user."""


def _clean(text: str) -> str:
    return _INVALID_XML.sub("", text)


def competition_to_xml(comp: Competition) -> ET.Element:
    root = ET.Element(
        "competition",
        {"class": _clean(comp.boat_class), "year": str(comp.year), "version": FORMAT_VERSION},
    )
    for day in comp.race_days:
        day_el = ET.SubElement(root, "raceday", {"name": _clean(day.name)})
        columns_el = ET.SubElement(day_el, "columns")
        for name in day.columns:
            ET.SubElement(columns_el, "column").text = _clean(name)
        for row in day.rows:
            row_el = ET.SubElement(day_el, "row")
            for value in row:
                ET.SubElement(row_el, "cell").text = _clean(value)
    return root


def competition_from_xml(root: ET.Element) -> Competition:
    if root.tag != "competition":
        raise StorageError("This is not a competition file (expected a <competition> element).")

    boat_class = root.get("class")
    year_text = root.get("year")
    if not boat_class or year_text is None:
        raise StorageError("The competition is missing its class or year.")
    try:
        year = int(year_text)
    except ValueError:
        raise StorageError(f"The year '{year_text}' is not a whole number.") from None

    try:
        comp = Competition(boat_class, year)
    except ValueError as exc:
        raise StorageError(str(exc)) from exc

    for index, day_el in enumerate(root.findall("raceday"), start=1):
        columns_el = day_el.find("columns")
        if columns_el is None:
            raise StorageError(f"Race day {index} has no <columns> element.")
        columns = [(c.text or "") for c in columns_el.findall("column")]
        rows = [[(c.text or "") for c in row_el.findall("cell")] for row_el in day_el.findall("row")]
        try:
            day = comp.add_race_day(day_el.get("name") or None)
            day.set_table(columns, rows)
        except ValueError as exc:
            raise StorageError(f"Race day {index}: {exc}") from exc
    return comp


def save_competition(comp: Competition, path) -> None:
    """Write the competition to path.

    The new file is written beside the old one first and then swapped into place, so a
    failure part-way through cannot leave a half-written competition file. The previous
    version is kept as '<name>.bak'.
    """
    path = Path(path)
    root = competition_to_xml(comp)
    ET.indent(root)
    tmp = path.with_name(path.name + ".tmp")
    try:
        ET.ElementTree(root).write(tmp, encoding="utf-8", xml_declaration=True)
        if path.exists():
            shutil.copy2(path, path.with_name(path.name + ".bak"))
        os.replace(tmp, path)
    except OSError as exc:
        raise StorageError(f"Could not save {path.name}: {exc.strerror or exc}") from exc
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


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
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", comp.boat_class).strip("_") or "competition"
    return f"{safe}_{comp.year}{EXTENSION}"


def list_competitions(folder) -> list[tuple[Path, Competition | None, str]]:
    """Every competition file in folder, as (path, competition, error).

    A file that cannot be read is still listed, with competition None and the reason in error.
    Sorted newest year first, then by boat class; unreadable files come last.
    """
    found = []
    for path in sorted(Path(folder).glob(f"*{EXTENSION}")):
        try:
            found.append((path, load_competition(path), ""))
        except StorageError as exc:
            found.append((path, None, str(exc)))
    return sorted(found, key=lambda f: (f[1] is None, -(f[1].year if f[1] else 0),
                                        (f[1].boat_class.upper() if f[1] else f[0].name)))


def rename_competition(path, boat_class: str, year: int) -> Path:
    """Change a competition's boat class and year, and rename its file to match.

    Returns the new path. Refuses (StorageError) if another competition already has that
    name. The backup (.bak) moves with the file.
    """
    path = Path(path)
    comp = load_competition(path)
    try:
        renamed = Competition(boat_class, year, comp.race_days)
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
