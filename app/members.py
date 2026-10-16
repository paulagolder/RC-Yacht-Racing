"""members.py - the club's sailors and their sail numbers, from RMBCSail.xml. No GUI code here.

The file lives in the data folder (~/.pyraceresults), one <sail> per boat:

    <sails>
      <sail sailnumber="   01" boatclass="VICTORIA" forename="Polly" surname="Breeze" club="RMBC" />
      <sail sailnumber="   02" boatclass="DF95" forename="Sam" surname="Tiller" club="RMBC" />
      ...
    </sails>

Every cell in a race day table must be the sail number of a sailor whose boat class is the
competition's boat class. Classes are matched ignoring case and spaces; sail numbers also
ignore leading zeros, so "1", "01" and "   01" are the same boat.
"""

from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .storage import StorageError

MEMBERS_FILE = "RMBCSail.xml"
DEFAULT_CLUB = "RMBC"
SAIL_NUMBER_WIDTH = 5      # new sail numbers are written right-aligned, like "   01"

_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!-- Club sailors. Add one <sail> for each boat; race results can only use these sail numbers.

  <sail sailnumber="   01" boatclass="DF95" forename="John" surname="Smith" club="RMBC" />
-->
<sails>
</sails>
"""


def _key(text: str) -> str:
    return "".join(text.split()).upper()


def _sail_key(text: str) -> str:
    key = _key(text)
    return (key.lstrip("0") or "0") if key.isdigit() else key


def format_sail_number(text: str) -> str:
    """'1' -> '   01', '123' -> '  123': at least two digits, right-aligned like the rest of the file."""
    text = text.strip()
    if text.isdigit():
        text = text.zfill(2)
    return text.rjust(SAIL_NUMBER_WIDTH)


@dataclass(frozen=True)
class Sailor:
    sail_number: str        # as written in the file, perhaps with leading spaces
    boat_class: str
    forename: str
    surname: str
    club: str = DEFAULT_CLUB

    @property
    def name(self) -> str:
        return f"{self.forename} {self.surname}".strip()

    @property
    def number(self) -> str:
        """The sail number without its padding, for showing on screen."""
        return self.sail_number.strip()

    @property
    def key(self) -> tuple[str, str]:
        return _key(self.boat_class), _sail_key(self.sail_number)


class MemberList:
    def __init__(self, sailors: list[Sailor], path: Path | None = None):
        self.sailors = sailors
        self.path = path
        self._index = {s.key: s for s in sailors}

    def find(self, sail_number: str, boat_class: str) -> Sailor | None:
        """The sailor with this sail number in this class, or None."""
        return self._index.get((_key(boat_class), _sail_key(sail_number)))


def check_table(rows: list[list[str]], members: MemberList,
                boat_class: str) -> list[tuple[int, int, str]]:
    """Problems in a race day table, as (row, column, message). Empty cells are allowed.

    A cell is wrong if its sail number is not a club sailor's in this class, or if the
    same sail number is already further up the same race (column).
    """
    problems = []
    seen: dict[tuple[int, str], int] = {}       # (column, sail number) -> row first seen
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            value = value.strip()
            if not value:
                continue
            if members.find(value, boat_class) is None:
                problems.append((r, c, f"No {boat_class} sailor has sail number '{value}'."))
            elif (c, _sail_key(value)) in seen:
                problems.append((r, c, f"Sail number '{value}' is already in row "
                                       f"{seen[(c, _sail_key(value))] + 1} of this race."))
            else:
                seen[(c, _sail_key(value))] = r
    return problems


def members_from_xml(root: ET.Element, path: Path | None = None) -> MemberList:
    if root.tag != "sails":
        raise StorageError(f"{MEMBERS_FILE} should contain a <sails> element.")
    sailors = []
    for number, el in enumerate(root.findall("sail"), start=1):
        sailor = Sailor(el.get("sailnumber", ""), el.get("boatclass", "").strip(),
                        el.get("forename", "").strip(), el.get("surname", "").strip(),
                        el.get("club", "").strip())
        problem = check_sailor([], sailor)
        if problem:
            raise StorageError(f"{MEMBERS_FILE}, sail {number}: {problem}")
        sailors.append(sailor)
    return MemberList(sailors, path)


def members_to_xml(sailors: list[Sailor]) -> ET.Element:
    root = ET.Element("sails")
    for s in sailors:
        ET.SubElement(root, "sail", {"sailnumber": s.sail_number, "boatclass": s.boat_class,
                                     "forename": s.forename, "surname": s.surname, "club": s.club})
    return root


def check_sailor(sailors: list[Sailor], sailor: Sailor, ignore: int | None = None) -> str | None:
    """Why this sailor cannot be added (or replace sailors[ignore]), or None if it can."""
    if not (sailor.number and sailor.boat_class.strip()):
        return "A sail needs a sail number and a boat class."
    if not sailor.name:
        return "A sail needs the sailor's forename or surname."
    for i, other in enumerate(sailors):
        if i != ignore and other.key == sailor.key:
            return f"{other.name} already has {other.boat_class} sail number {other.number}."
    return None


def save_members(sailors: list[Sailor], data_dir) -> None:
    """Write data_dir/RMBCSail.xml, keeping the previous version as RMBCSail.xml.bak.

    Like competition files, it is written beside the old file and then swapped into place.
    Raises StorageError.
    """
    path = Path(data_dir) / MEMBERS_FILE
    root = members_to_xml(sailors)
    ET.indent(root)
    tmp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
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


def load_members(data_dir) -> MemberList:
    """Read data_dir/RMBCSail.xml, creating an empty one if it is missing. Raises StorageError."""
    path = Path(data_dir) / MEMBERS_FILE
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_TEMPLATE, encoding="utf-8")
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise StorageError(f"{path} is not valid XML: {exc}") from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc.strerror or exc}") from exc
    return members_from_xml(root, path)
