"""settings_store.py - the settings: the data folder and its properties.xml.

Competition files live in ~/.pyraceresults by default. That folder also holds properties.xml:

    <properties>
      <title>RC Yacht Race Tables</title>
      <default_rows>5</default_rows>
      <default_columns>4</default_columns>
      <output_folder>~/Documents/raceresult_output</output_folder>
    </properties>

output_folder is where Export HTML writes, in a sub folder named after the competition file
(for example ~/Documents/raceresult_output/DF95_2026/). ~ and $VARIABLES are expanded. A
relative folder ("output") is in the folder that holds the data folder.

A portable copy (on a USB stick, say) keeps everything together:

    RC-Yacht-Racing/
        pyraceresults        the program
        output/              the exported web pages: the only folder a user needs
        system/              the data folder: properties.xml, the sailors, the competitions

The program uses a system folder beside it as its data folder (find_data_dir), with the
default output_folder "output".

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
SYSTEM_FOLDER = "system"                 # beside the program: a portable copy's data folder
PORTABLE_OUTPUT_FOLDER = "output"        # beside the program, in a portable copy
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
        """The output folder; a relative one is beside the data folder."""
        return self.data_dir.parent / os.path.expandvars(os.path.expanduser(self.output_folder))


def find_data_dir(program_dir) -> Path:
    """The system folder beside the program if there is one (a portable copy), otherwise
    ~/.pyraceresults."""
    system = Path(program_dir) / SYSTEM_FOLDER
    return system if system.is_dir() else DATA_DIR


def _default_output(data_dir: Path) -> str:
    return PORTABLE_OUTPUT_FOLDER if data_dir.name == SYSTEM_FOLDER else DEFAULT_OUTPUT_FOLDER


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
        output_folder=(root.findtext("output_folder") or "").strip() or _default_output(data_dir),
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
    defaults = Settings(data_dir, output_folder=_default_output(data_dir))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            root = settings_to_xml(defaults)
            ET.indent(root)
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
        return settings_from_xml(parse_xml(path), data_dir)
    except (OSError, ET.ParseError):
        return defaults
