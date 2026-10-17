"""browser.py - showing an exported page in the web browser."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path


def open_in_browser(path: Path) -> None:
    """Show a file in the web browser.

    The packaged program (PyInstaller) points LD_LIBRARY_PATH at its own libraries, which can
    stop the browser from starting, so on Linux the original setting is put back first.
    """
    opener = shutil.which("xdg-open") if sys.platform.startswith("linux") else None
    if opener is None:
        webbrowser.open(path.as_uri())
        return
    env = dict(os.environ)
    if "LD_LIBRARY_PATH_ORIG" in env:
        env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
    elif getattr(sys, "frozen", False):
        env.pop("LD_LIBRARY_PATH", None)
    subprocess.Popen([opener, str(path)], env=env, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
