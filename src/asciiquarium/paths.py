"""User data directory resolver.

Single source of truth for where the launch counter, logbook, and any future
on-disk user state lives. No third-party dependency: we follow the same
platform conventions ``platformdirs`` would but without the import cost.

Kept pygame-free so the lower simulation layers can use it freely.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_APP_NAME = "asciiquarium"


def user_data_dir() -> Path:
    """Return (and lazily create) the OS-appropriate user data directory.

    * Windows: ``%APPDATA%\\asciiquarium``
    * macOS:   ``~/Library/Application Support/asciiquarium``
    * Linux/other: ``$XDG_DATA_HOME/asciiquarium`` or ``~/.local/share/asciiquarium``
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(base) / _APP_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / _APP_NAME
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(base) / _APP_NAME
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        # If the OS refuses (e.g. read-only home), fall back to a tmp path so
        # callers still get a usable Path. Persistence is best-effort.
        path = Path(os.environ.get("TMPDIR", "/tmp")) / _APP_NAME
        path.mkdir(parents=True, exist_ok=True)
    return path


def launch_counter_path() -> Path:
    return user_data_dir() / "launches.txt"


def logbook_path() -> Path:
    return user_data_dir() / "logbook.json"


def bump_launch_counter() -> int:
    """Increment and return the persistent launch counter.

    Best-effort: on any I/O failure we return 1 so callers can keep going.
    """
    p = launch_counter_path()
    try:
        current = int(p.read_text(encoding="utf-8").strip()) if p.exists() else 0
    except (OSError, ValueError):
        current = 0
    current += 1
    try:
        p.write_text(str(current), encoding="utf-8")
    except OSError:
        pass
    return current


def read_launch_counter() -> int:
    """Read the launch counter without bumping it (for tests / display)."""
    p = launch_counter_path()
    try:
        return int(p.read_text(encoding="utf-8").strip()) if p.exists() else 0
    except (OSError, ValueError):
        return 0
