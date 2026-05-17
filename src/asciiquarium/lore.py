"""Lore fragment system.

Tiny one-line atmospheric messages with hard frequency caps. The mystery
works because it shuts up most of the time. No network, no analytics —
fragments are picked from a static in-memory table.

Pygame-free. The renderer is responsible for actually displaying the
returned text; this module only decides *whether* and *what* to emit.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class LoreFragment:
    """A single lore line and its semantic tag."""

    tag: str  # one of: "signal", "archive", "sonar", "depth"
    text: str


# Hard frequency caps. Mood/event presets may scale ``min_interval`` down,
# but never below MIN_FLOOR.
MIN_FLOOR: float = 30.0
DEFAULT_MIN_INTERVAL: float = 180.0  # one fragment every ~3 minutes at most
DEFAULT_BURST_GUARD: float = 45.0  # never two within 45 seconds


FRAGMENTS: tuple[LoreFragment, ...] = (
    LoreFragment("signal", "[signal] something below is counting"),
    LoreFragment("signal", "[signal] return waveform inverted at 03:41"),
    LoreFragment("signal", "[signal] carrier wave attributed to no fleet"),
    LoreFragment("archive", "[archive] lighthouse 7 stopped responding"),
    LoreFragment("archive", "[archive] log #1188: tank temperature anomalous"),
    LoreFragment("archive", "[archive] crew manifest withdrawn from public index"),
    LoreFragment("sonar", "[sonar] return pattern does not match known fauna"),
    LoreFragment("sonar", "[sonar] echo persists after source removed"),
    LoreFragment("sonar", "[sonar] benthic mass moving against current"),
    LoreFragment("depth", "[depth] pressure warning ignored"),
    LoreFragment("depth", "[depth] -3140m :: ambient light source unexplained"),
    LoreFragment("depth", "[depth] thermocline shifted 11m overnight"),
)


@dataclass
class LoreState:
    """Mutable cooldown bookkeeping for lore emission."""

    # Seconds until the next eligible emission (counts down each tick).
    next_eligible: float = DEFAULT_MIN_INTERVAL
    # Seconds since the last actual emission (counts up each tick). Used to
    # enforce :data:`DEFAULT_BURST_GUARD`.
    since_last: float = 1e9
    enabled: bool = True
    # The most recently emitted fragment (renderer reads + clears this).
    pending: LoreFragment | None = None
    # How long the renderer should keep showing ``pending`` (in seconds).
    visible_for: float = 0.0


def tick(
    state: LoreState,
    dt: float,
    rng: random.Random,
    *,
    preferred_tags: frozenset[str] | None = None,
    min_interval: float = DEFAULT_MIN_INTERVAL,
    burst_guard: float = DEFAULT_BURST_GUARD,
) -> LoreFragment | None:
    """Advance the lore clock and maybe emit a fragment.

    Returns the emitted :class:`LoreFragment` (also stored on ``state.pending``)
    or ``None`` if no fragment fires this tick.
    """
    state.since_last += dt
    if state.visible_for > 0:
        state.visible_for = max(0.0, state.visible_for - dt)
    if not state.enabled:
        return None
    state.next_eligible -= dt
    if state.next_eligible > 0:
        return None
    if state.since_last < max(MIN_FLOOR, burst_guard):
        # Even though the cooldown elapsed, refuse to stack two messages.
        state.next_eligible = max(MIN_FLOOR, burst_guard) - state.since_last
        return None

    fragment = _pick_fragment(rng, preferred_tags)
    state.pending = fragment
    state.since_last = 0.0
    state.visible_for = 6.0
    # Reset cooldown with jitter so the rhythm isn't perfectly regular.
    interval = max(MIN_FLOOR, min_interval)
    state.next_eligible = rng.uniform(interval, interval * 1.8)
    return fragment


def _pick_fragment(
    rng: random.Random,
    preferred_tags: frozenset[str] | None,
) -> LoreFragment:
    """Weighted pick: preferred-tag fragments get 3x weight."""
    weights: list[float] = []
    for f in FRAGMENTS:
        if preferred_tags and f.tag in preferred_tags:
            weights.append(3.0)
        else:
            weights.append(1.0)
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for f, w in zip(FRAGMENTS, weights):
        acc += w
        if r <= acc:
            return f
    return FRAGMENTS[-1]


def force_emit(state: LoreState, rng: random.Random) -> LoreFragment:
    """Emit a fragment right now, bypassing cooldowns (used by ``--pin``)."""
    fragment = _pick_fragment(rng, None)
    state.pending = fragment
    state.since_last = 0.0
    state.visible_for = 6.0
    return fragment
