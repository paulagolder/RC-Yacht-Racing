"""settings_store.py - the settings: the data folder and its properties.xml.

Competition files live in ~/.pyraceresults by default. That folder also holds properties.xml:

    <properties>
      <title>RC Yacht Race Tables</title>
      <default_rows>5</default_rows>
      <default_columns>4</default_columns>
      <output_folder>~/Documents/raceresult_output</output_folder>
    </properties>

output_folder is where Export HTML writes, in a sub folder named after the competition file
(for example ~/Documents/raceresult_output/DF95_2026/). ~ and $VARIABLES are expanded.

The folder and file are created with these defaults the first time the program runs. A missing
or unreadable value falls back to its default, and numbers are kept within the limits in
model/limits.py.
"""

from __future__ import annotations

import os
# Files are only read through xml_file.parse_xml, which refuses XML bombs.
import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import dataclass
from pathlib import Path

from ..model.limits import DEFAULT_RACES, DEFAULT_ROWS, MAX_PLACES, MAX_RACES
from .xml_file import parse_xml

DATA_DIR = Path.home() / ".pyraceresults"
PROPERTIES_FILE = "properties.xml"
DEFAULT_TITLE = "RC Yacht Race Tables"
DEFAULT_OUTPUT_FOLDER = "~/Documents/raceresult_output"
LOGO_FILE = Path(__file__).parent.parent / "resources" / "club_logo.png"   # made from club_logo.svg


@dataclass
class Settings:
    data_dir: Path
    title: str = DEFAULT_TITLE
    default_rows: int = DEFAULT_ROWS
    default_columns: int = DEFAULT_RACES             # races in a new race day
    output_folder: str = DEFAULT_OUTPUT_FOLDER       # as written in the file, perhaps with ~

    @property
    def output_dir(self) -> Path:
        return Path(os.path.expandvars(os.path.expanduser(self.output_folder)))


def _number(root: ET.Element, tag: str, default: int, maximum: int) -> int:
    try:
        return min(max(int((root.findtext(tag) or "").strip()), 1), maximum)
    except ValueError:
        return default


def settings_from_xml(root: ET.Element, data_dir: Path) -> Settings:
    return Settings(
        data_dir=data_dir,
        title=(root.findtext("title") or "").strip() or DEFAULT_TITLE,
        default_rows=_number(root, "default_rows", DEFAULT_ROWS, MAX_PLACES),
        default_columns=_number(root, "default_columns", DEFAULT_RACES, MAX_RACES),
        output_folder=(root.findtext("output_folder") or "").strip() or DEFAULT_OUTPUT_FOLDER,
    )


def settings_to_xml(settings: Settings) -> ET.Element:
    root = ET.Element("properties")
    ET.SubElement(root, "title").text = settings.title
    ET.SubElement(root, "default_rows").text = str(settings.default_rows)
    ET.SubElement(root, "default_columns").text = str(settings.default_columns)
    ET.SubElement(root, "output_folder").text = settings.output_folder
    return root


def load_settings(data_dir=DATA_DIR) -> Settings:
    """Read data_dir/properties.xml, creating the folder and a default file if they are missing.

    Never raises: if the file cannot be read or written, the defaults are used.
    """
    data_dir = Path(data_dir)
    path = data_dir / PROPERTIES_FILE
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            root = settings_to_xml(Settings(data_dir))
            ET.indent(root)
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        return settings_from_xml(parse_xml(path), data_dir)
    except (OSError, ET.ParseError):
        return Settings(data_dir)
