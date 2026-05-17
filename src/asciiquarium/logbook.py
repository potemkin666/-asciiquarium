"""Local discovery logbook.

Tiny JSON file under :func:`asciiquarium.paths.user_data_dir`. Records the
first-seen wall-clock timestamp for each creature/event so the user gets a
gentle sense of "Abyssarium remembers what you've seen".

No network, no accounts, no cloud. Pygame-free.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .paths import logbook_path

# Canonical entry names + a human-friendly display name.
# Add new entries here when shipping new rare creatures or events.
KNOWN_ENTRIES: dict[str, str] = {
    # Common
    "fish": "Glassfish",
    "bubble": "Bubble",
    "turtle": "Sea Turtle",
    "koi": "Koi (錦鯉)",
    # Rare creatures
    "giant_squid": "Giant Squid",
    "ghost_whale": "Ghost Whale",
    "skeletal_coelacanth": "Skeletal Coelacanth",
    "deep_sea_angel": "Deep-Sea Angel",
    "submarine_wreck": "Submarine Wreck",
    "the_thing_below": "The Thing Below",
    "black_koi": "Black Koi",
    "the_sleeper": "The Sleeper",  # one-in-666 launches
    # Events
    "BLACK_CURRENT": "Black Current",
    "WHALE_SONG": "Whale Song",
    "ABYSSAL_BLOOM": "Abyssal Bloom",
    "GHOST_SHIP": "Ghost Ship",
    "SURFACE_STORM": "Surface Storm",
    "OLD_SIGNAL": "Old Signal",
}


@dataclass
class Logbook:
    """In-memory logbook + path it serialises to. ``path=None`` disables I/O."""

    entries: dict[str, float] = field(default_factory=dict)
    path: Path | None = None

    def record(self, key: str, now: float | None = None) -> bool:
        """Record ``key`` if not already seen. Returns True if new."""
        if key in self.entries:
            return False
        self.entries[key] = now if now is not None else time.time()
        self.save()
        return True

    def has(self, key: str) -> bool:
        return key in self.entries

    def known_count(self) -> int:
        return len(self.entries)

    def all_entries(self) -> list[tuple[str, str, float | None]]:
        """Return ``(key, display_name, first_seen_or_None)`` for every known slot."""
        out: list[tuple[str, str, float | None]] = []
        for key, display in KNOWN_ENTRIES.items():
            out.append((key, display, self.entries.get(key)))
        return out

    def save(self) -> None:
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps({"entries": self.entries}, indent=2),
                encoding="utf-8",
            )
        except OSError:
            # Best-effort persistence.
            pass

    @classmethod
    def load(cls, path: Path | None = None) -> Logbook:
        path = path if path is not None else logbook_path()
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                entries = data.get("entries", {}) if isinstance(data, dict) else {}
                if not isinstance(entries, dict):
                    entries = {}
                # Coerce timestamps to float; drop garbage.
                clean: dict[str, float] = {}
                for k, v in entries.items():
                    if isinstance(k, str):
                        try:
                            clean[k] = float(v)
                        except (TypeError, ValueError):
                            continue
                return cls(entries=clean, path=path)
        except (OSError, ValueError):
            pass
        return cls(entries={}, path=path)


def in_memory() -> Logbook:
    """A logbook that never touches disk (handy for tests / pure runs)."""
    return Logbook(entries={}, path=None)
