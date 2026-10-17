"""xml_file.py - writing an XML file without ever leaving a half-written one."""

from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from .errors import StorageError


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
