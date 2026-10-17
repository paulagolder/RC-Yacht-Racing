"""member_store.py - read and write the club's sailors, RMBCSail.xml.

The file lives in the data folder (~/.pyraceresults), one <sail> per boat:

    <sails>
      <sail sailnumber="   01" boatclass="VICTORIA" forename="Polly" surname="Breeze" club="RMBC"
            tag="PB" />
      <sail sailnumber="   02" boatclass="DF95" forename="Sam" surname="Tiller" club="RMBC" tag="ST" />
      ...
    </sails>

tag tells sailors apart when sail numbers clash across classes; left out, it is the initials.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ..model.member_list import MemberList
from ..model.sailor import Sailor
from .errors import StorageError
from .xml_file import write_xml

MEMBERS_FILE = "RMBCSail.xml"

_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!-- Club sailors. Add one <sail> for each boat; race results can only use these sail numbers.

  <sail sailnumber="   01" boatclass="DF95" forename="John" surname="Smith" club="RMBC" />
-->
<sails>
</sails>
"""


def members_from_xml(root: ET.Element, path: Path | None = None) -> MemberList:
    if root.tag != "sails":
        raise StorageError(f"{MEMBERS_FILE} should contain a <sails> element.")
    sailors = []
    for number, el in enumerate(root.findall("sail"), start=1):
        sailor = Sailor(el.get("sailnumber", ""), el.get("boatclass", "").strip(),
                        el.get("forename", "").strip(), el.get("surname", "").strip(),
                        el.get("club", "").strip(), el.get("tag", ""))
        problem = sailor.problem()
        if problem:
            raise StorageError(f"{MEMBERS_FILE}, sail {number}: {problem}")
        sailors.append(sailor)
    return MemberList(sailors, path)


def members_to_xml(members: MemberList) -> ET.Element:
    root = ET.Element("sails")
    for s in members.sailors:
        ET.SubElement(root, "sail", {"sailnumber": s.sail_number, "boatclass": s.boat_class,
                                     "forename": s.forename, "surname": s.surname, "club": s.club,
                                     "tag": s.tag})
    return root


def save_members(members: MemberList, data_dir) -> None:
    """Write data_dir/RMBCSail.xml, keeping the previous version as RMBCSail.xml.bak.

    Like competition files, it is written beside the old file and then swapped into place.
    Raises StorageError.
    """
    write_xml(members_to_xml(members), Path(data_dir) / MEMBERS_FILE, make_folder=True)


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
