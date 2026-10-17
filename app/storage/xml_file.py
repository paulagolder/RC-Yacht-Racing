"""xml_file.py - reading XML files safely, and writing them without ever leaving a half-written one.

parse_xml refuses a file with a <!DOCTYPE> or <!ENTITY> declaration. Those are how "XML bomb"
attacks work (a small crafted file that expands until the computer runs out of memory), and the
program's own files never have one. Files that are not UTF-8 (UTF-16, say, where the check could
be dodged) are refused too.
"""

from __future__ import annotations

import os
import re
import shutil
# Every file is read through parse_xml below, which refuses XML bombs.
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

from .errors import StorageError


_DECLARATION = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


def parse_xml(path) -> ET.Element:
    """Read an XML file and return its root element.

    Raises OSError if it cannot be read, or ET.ParseError if it is not valid XML, is not UTF-8,
    or has a <!DOCTYPE> or <!ENTITY> declaration.
    """
    data = Path(path).read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in data:
        raise ET.ParseError("it is not a UTF-8 file")
    if _DECLARATION.search(data):
        raise ET.ParseError("it has a <!DOCTYPE> or <!ENTITY> declaration, which is not allowed")
    # DOCTYPE and ENTITY declarations were refused above, so this cannot be an XML bomb.
    return ET.fromstring(data)  # nosec B314


def write_xml(root: ET.Element, path: Path, make_folder: bool = False) -> None:
    """Write root to path, keeping the previous version as '<name>.bak'.

    The new file is written beside the old one first and then swapped into place, so a
    failure part-way through cannot leave a half-written file. Raises StorageError.
    """
    ET.indent(root)
    tmp = path.with_name(path.name + ".tmp")
    try:
        if make_folder:
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
