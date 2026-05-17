"""Central :class:`AquariumState` threaded through every tick.

Holds mood, active event scalars, lore cadence, sonar/food bookkeeping,
RNG, and a reference to the persistent logbook. Pygame-free: the renderer
reads these fields each frame and translates them into pixels, but never
mutates them directly (key handlers call dedicated mutator methods).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .events import (
    DEFAULT_MIN_GAP,
    EventEffects,
    EventScheduler,
)
from .logbook import Logbook, in_memory
from .lore import DEFAULT_MIN_INTERVAL, LoreState
from .moods import CALM, DEFAULT_TRANSITION_PERIOD


@dataclass
class AquariumState:
    """Mutable, single-owner state for one running aquarium.

    Most fields default to inert values so a "classic mode" aquarium that
    never enables moods/events behaves exactly like before.
    """

    # Mood
    mood: str = CALM
    mood_pinned: bool = True
    mood_clock: float = DEFAULT_TRANSITION_PERIOD
    mood_period: float = DEFAULT_TRANSITION_PERIOD

    # Events
    events_enabled: bool = False
    event_effects: EventEffects = field(default_factory=EventEffects)
    event_scheduler: EventScheduler = field(default_factory=EventScheduler)
    last_event_name: str = ""

    # Lore
    lore: LoreState = field(default_factory=LoreState)
    lore_visible: bool = True  # user toggle ("l" key)

    # Rare creatures
    rare_creatures_enabled: bool = False
    sonar_pings: int = 0  # cumulative across the session
    last_sonar_at: float = -1e9
    food_drops: int = 0
    food_x: float = 0.0  # most recent food location (renderer can draw it)
    food_y: float = 0.0
    food_visible_for: float = 0.0

    # Launch / 666 gate
    launch_count: int = 0

    # Logbook (defaults to an in-memory log that doesn't touch disk)
    logbook: Logbook = field(default_factory=in_memory)

    # Tick counter / wallclock-ish sim time (seconds since aquarium start)
    sim_time: float = 0.0

    # Injected RNG; never call ``random.random()`` directly.
    rng: random.Random = field(default_factory=random.Random)

    # CRT / nightwatch flags read by renderer.
    crt_scanlines: bool = False

    # -- mutator helpers (called from renderer key handlers) ---------------

    def pin_mood(self, name: str) -> None:
        self.mood = name
        self.mood_pinned = True

    def set_mood(self, name: str) -> None:
        """Cycle/set mood without pinning (still allowed to transition)."""
        self.mood = name

    def record_sonar(self) -> None:
        self.sonar_pings += 1
        self.last_sonar_at = self.sim_time

    def record_food(self, x: float, y: float) -> None:
        self.food_drops += 1
        self.food_x = float(x)
        self.food_y = float(y)
        self.food_visible_for = 6.0


def make_default_state(
    *,
    rng: random.Random,
    mood: str = CALM,
    mood_pinned: bool = True,
    events_enabled: bool = False,
    rare_creatures_enabled: bool = False,
    lore_enabled: bool = False,
    event_min_gap: float = DEFAULT_MIN_GAP,
    lore_min_interval: float = DEFAULT_MIN_INTERVAL,
    logbook: Logbook | None = None,
    launch_count: int = 0,
    crt_scanlines: bool = False,
) -> AquariumState:
    """Build a fully-wired AquariumState.

    Keyword arguments mirror what :func:`asciiquarium.modes.resolve` returns
    so wiring is one short hop.
    """
    st = AquariumState(rng=rng)
    st.mood = mood
    st.mood_pinned = mood_pinned
    st.events_enabled = events_enabled
    st.rare_creatures_enabled = rare_creatures_enabled
    st.lore.enabled = lore_enabled
    st.event_scheduler.enabled = events_enabled
    st.event_scheduler.min_gap = event_min_gap
    st.event_scheduler.cooldown = event_min_gap
    st.lore.next_eligible = lore_min_interval
    if logbook is not None:
        st.logbook = logbook
    st.launch_count = launch_count
    st.crt_scanlines = crt_scanlines
    return st
