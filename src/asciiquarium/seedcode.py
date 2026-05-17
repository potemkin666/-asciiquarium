"""Seed-share codes.

Tank code format: ``BIOME-SEED-MOOD[-MODIFIER]`` (case-insensitive,
hyphen-separated). Lets users share interesting tanks like::

    abyssarium --code TRENCH-777-HAUNTED-KOI

The modifier is one of: ``KOI``, ``SUMI``, ``SPRING``, ``NIGHTWATCH``
(or empty).
"""

from __future__ import annotations

from dataclasses import dataclass

from .moods import is_valid_mood

_VALID_BIOMES = {"reef", "abyss", "kelp-forest", "arctic", "trench", "default"}
_VALID_MODIFIERS = {"", "KOI", "SUMI", "SPRING", "NIGHTWATCH"}


@dataclass(frozen=True)
class SeedCode:
    biome: str
    seed: int
    mood: str
    modifier: str = ""

    def serialize(self) -> str:
        parts = [self.biome.upper(), str(self.seed), self.mood.upper()]
        if self.modifier:
            parts.append(self.modifier.upper())
        return "-".join(parts)


def parse(code: str) -> SeedCode:
    """Parse a tank code. Raises ``ValueError`` on malformed input."""
    if not isinstance(code, str) or not code.strip():
        raise ValueError("empty tank code")
    parts = code.strip().split("-")
    if len(parts) < 3 or len(parts) > 4:
        raise ValueError(f"tank code must have 3 or 4 fields, got {len(parts)}")
    biome_raw, seed_raw, mood_raw = parts[0], parts[1], parts[2]
    modifier_raw = parts[3] if len(parts) == 4 else ""

    biome = biome_raw.lower()
    if biome not in _VALID_BIOMES:
        raise ValueError(f"unknown biome {biome_raw!r}; valid: {sorted(_VALID_BIOMES)}")
    try:
        seed = int(seed_raw)
    except ValueError as exc:
        raise ValueError(f"seed must be an integer, got {seed_raw!r}") from exc
    mood = mood_raw.lower()
    if not is_valid_mood(mood):
        raise ValueError(f"unknown mood {mood_raw!r}")
    modifier = modifier_raw.upper()
    if modifier not in _VALID_MODIFIERS:
        raise ValueError(f"unknown modifier {modifier_raw!r}")
    return SeedCode(biome=biome, seed=seed, mood=mood, modifier=modifier)
