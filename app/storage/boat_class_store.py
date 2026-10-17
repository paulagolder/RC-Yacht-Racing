"""boat_class_store.py - read and write the club's boat classes, yachtclasses.xml.

The file lives in the data folder (~/.pyraceresults), one <boatclass> per class:

    <classes>
      <boatclass key="df65" fullname="DF65" cypher="65" symbol="#" />
      <boatclass key="rg65" fullname="RG65" cypher="rg" symbol="$" />
      <boatclass key="df95" fullname="DF95" cypher="95" symbol="@" />
      <boatclass key="victoria" fullname="Victoria" cypher="Va" symbol="*" />
    </classes>

If the file is missing it is created with these four classes.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ..model.boat_class import BOAT_CLASSES, DEFAULT_BOAT_CLASSES, BoatClass, BoatClassList
from .errors import StorageError
from .xml_file import write_xml

BOAT_CLASSES_FILE = "yachtclasses.xml"


def boat_classes_from_xml(root: ET.Element) -> BoatClassList:
    if root.tag != "classes":
        raise StorageError(f"{BOAT_CLASSES_FILE} should contain a <classes> element.")
    classes = BoatClassList()
    for number, el in enumerate(root.findall("boatclass"), start=1):
        boat_class = BoatClass(el.get("key", "").strip(), el.get("fullname", "").strip(),
                               el.get("cypher", "").strip(), el.get("symbol", "").strip())
        try:
            classes.add(boat_class)
        except ValueError as exc:
            raise StorageError(f"{BOAT_CLASSES_FILE}, class {number}: {exc}") from exc
    return classes


def boat_classes_to_xml(classes: BoatClassList) -> ET.Element:
    root = ET.Element("classes")
    for c in classes.classes:
        ET.SubElement(root, "boatclass", {"key": c.key, "fullname": c.fullname,
                                          "cypher": c.cypher, "symbol": c.symbol})
    return root


def save_boat_classes(classes: BoatClassList, data_dir) -> None:
    """Write data_dir/yachtclasses.xml, keeping the previous version as yachtclasses.xml.bak.

    Raises StorageError.
    """
    write_xml(boat_classes_to_xml(classes), Path(data_dir) / BOAT_CLASSES_FILE, make_folder=True)


def load_boat_classes(data_dir) -> BoatClassList:
    """Read data_dir/yachtclasses.xml, creating it with the default classes if it is missing.

    Raises StorageError.
    """
    path = Path(data_dir) / BOAT_CLASSES_FILE
    if not path.exists():
        save_boat_classes(BoatClassList(DEFAULT_BOAT_CLASSES), data_dir)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise StorageError(f"{path} is not valid XML: {exc}") from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc.strerror or exc}") from exc
    return boat_classes_from_xml(root)


def boat_class_names(data_dir) -> list[str]:
    """The class names for the class boxes on screen. Never raises: falls back to the defaults."""
    try:
        return load_boat_classes(data_dir).names() or list(BOAT_CLASSES)
    except StorageError:
        return list(BOAT_CLASSES)
