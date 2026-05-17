"""Mood system.

Moods are slow-moving atmospheric states that bias spawn rates, palettes,
which events can fire, and which lore tags are eligible. Mood transitions
are driven by a weighted Markov-ish step on a slow clock (tens of seconds),
so the user perceives them as ambience, not gameplay.

Pygame-free; uses an injected ``random.Random`` for full determinism.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# Canonical mood names. Strings (not Enum) keep CLI / JSON wiring trivial.
CALM = "calm"
STORMING = "storming"
HAUNTED = "haunted"
BIOLUMINESCENT = "bioluminescent"
POLLUTED = "polluted"
DREAMING = "dreaming"
ABYSSAL = "abyssal"
FESTIVAL = "festival"

ALL_MOODS: tuple[str, ...] = (
    CALM,
    STORMING,
    HAUNTED,
    BIOLUMINESCENT,
    POLLUTED,
    DREAMING,
    ABYSSAL,
    FESTIVAL,
)


@dataclass(frozen=True)
class MoodSpec:
    """Tunables for a single mood."""

    name: str
    # Multiplicative modifiers on top of base spawn rates.
    fish_spawn_mult: float = 1.0
    bubble_density_mult: float = 1.0
    rare_creature_mult: float = 1.0
    # Event names this mood enables (others are gated off).
    allowed_events: frozenset[str] = field(default_factory=frozenset)
    # Lore tags this mood prefers (others can still fire at lower weight).
    preferred_lore_tags: frozenset[str] = field(default_factory=frozenset)
    # Optional palette tint (RGB delta added to drawn glyphs at the renderer).
    # Kept here as data so renderer can read it without engine cross-imports.
    tint: tuple[int, int, int] = (0, 0, 0)


MOODS: dict[str, MoodSpec] = {
    CALM: MoodSpec(
        name=CALM,
        fish_spawn_mult=1.0,
        bubble_density_mult=1.0,
        rare_creature_mult=1.0,
        allowed_events=frozenset({"WHALE_SONG"}),
        preferred_lore_tags=frozenset({"archive"}),
    ),
    STORMING: MoodSpec(
        name=STORMING,
        fish_spawn_mult=0.7,
        bubble_density_mult=2.0,
        rare_creature_mult=0.5,
        allowed_events=frozenset({"SURFACE_STORM", "GHOST_SHIP"}),
        preferred_lore_tags=frozenset({"depth", "sonar"}),
        tint=(-10, -10, 0),
    ),
    HAUNTED: MoodSpec(
        name=HAUNTED,
        fish_spawn_mult=0.5,
        bubble_density_mult=0.6,
        rare_creature_mult=2.0,
        allowed_events=frozenset({"GHOST_SHIP", "OLD_SIGNAL", "BLACK_CURRENT"}),
        preferred_lore_tags=frozenset({"signal", "archive"}),
        tint=(-20, -10, -5),
    ),
    BIOLUMINESCENT: MoodSpec(
        name=BIOLUMINESCENT,
        fish_spawn_mult=1.1,
        bubble_density_mult=1.4,
        rare_creature_mult=1.7,
        allowed_events=frozenset({"ABYSSAL_BLOOM", "WHALE_SONG"}),
        preferred_lore_tags=frozenset({"depth"}),
        tint=(0, 20, 20),
    ),
    POLLUTED: MoodSpec(
        name=POLLUTED,
        fish_spawn_mult=0.5,
        bubble_density_mult=1.2,
        rare_creature_mult=0.3,
        allowed_events=frozenset({"BLACK_CURRENT"}),
        preferred_lore_tags=frozenset({"archive", "depth"}),
        tint=(15, 5, -10),
    ),
    DREAMING: MoodSpec(
        name=DREAMING,
        fish_spawn_mult=0.8,
        bubble_density_mult=0.8,
        rare_creature_mult=1.4,
        allowed_events=frozenset({"WHALE_SONG", "OLD_SIGNAL"}),
        preferred_lore_tags=frozenset({"signal", "depth"}),
        tint=(10, -5, 15),
    ),
    ABYSSAL: MoodSpec(
        name=ABYSSAL,
        fish_spawn_mult=0.4,
        bubble_density_mult=0.5,
        rare_creature_mult=2.5,
        allowed_events=frozenset({"BLACK_CURRENT", "OLD_SIGNAL", "ABYSSAL_BLOOM"}),
        preferred_lore_tags=frozenset({"depth", "sonar", "signal"}),
        tint=(-15, -10, -5),
    ),
    FESTIVAL: MoodSpec(
        name=FESTIVAL,
        fish_spawn_mult=1.3,
        bubble_density_mult=1.5,
        rare_creature_mult=1.2,
        allowed_events=frozenset({"WHALE_SONG"}),
        preferred_lore_tags=frozenset({"archive"}),
        tint=(15, 10, 0),
    ),
}


# Default transition weights. Higher = more likely to move to that mood when
# the slow clock fires. ``calm`` is the gravitational center: every mood has
# at least some chance to drift back. Self-weight keeps the current mood from
# changing every tick.
_DEFAULT_TRANSITIONS: dict[str, dict[str, float]] = {
    CALM: {CALM: 6.0, STORMING: 1.0, BIOLUMINESCENT: 1.0, DREAMING: 1.0, POLLUTED: 0.4},
    STORMING: {STORMING: 4.0, CALM: 3.0, HAUNTED: 1.5, POLLUTED: 0.8},
    HAUNTED: {HAUNTED: 4.0, CALM: 2.0, ABYSSAL: 1.5, DREAMING: 0.8},
    BIOLUMINESCENT: {BIOLUMINESCENT: 4.0, CALM: 2.0, DREAMING: 1.5, ABYSSAL: 1.0},
    POLLUTED: {POLLUTED: 3.0, CALM: 3.0, STORMING: 1.0},
    DREAMING: {DREAMING: 4.0, CALM: 2.0, BIOLUMINESCENT: 1.5, HAUNTED: 1.0},
    ABYSSAL: {ABYSSAL: 4.0, HAUNTED: 1.5, CALM: 1.0, BIOLUMINESCENT: 1.0},
    FESTIVAL: {FESTIVAL: 3.0, CALM: 4.0},
}


# Slow-clock period in seconds. Moods reconsider transitions on this cadence.
DEFAULT_TRANSITION_PERIOD: float = 90.0


def pick_next_mood(
    current: str,
    rng: random.Random,
    *,
    transitions: dict[str, dict[str, float]] | None = None,
) -> str:
    """Return the next mood given the current one and an RNG.

    Pure function: no side effects, no module-level RNG. Uses the
    ``transitions`` table if provided, otherwise the default.
    """
    table = transitions if transitions is not None else _DEFAULT_TRANSITIONS
    row = table.get(current) or {current: 1.0}
    names = list(row.keys())
    weights = [max(0.0, row[n]) for n in names]
    total = sum(weights)
    if total <= 0:
        return current
    r = rng.random() * total
    acc = 0.0
    for n, w in zip(names, weights):
        acc += w
        if r <= acc:
            return n
    return names[-1]


def get_mood(name: str) -> MoodSpec:
    """Lookup with safe fallback to ``calm`` for unknown names."""
    return MOODS.get(name, MOODS[CALM])


def is_valid_mood(name: str) -> bool:
    return name in MOODS
