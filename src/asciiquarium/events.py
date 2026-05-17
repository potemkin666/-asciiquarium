"""Event system.

Events are short-lived atmospheric modifiers. They never mutate sprites or
the scene directly: they expose *scalars* (palette tint, spawn-rate
multiplier, flicker flag, overlay text, sound cue) that the aquarium and
renderer read each frame. Mood gates which events can fire.

Each event subclasses :class:`Event` and overrides ``on_start`` /
``on_tick`` / ``on_end``. All events are deterministic given an injected
:class:`random.Random`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .state import AquariumState


# Canonical event identifiers.
BLACK_CURRENT = "BLACK_CURRENT"
WHALE_SONG = "WHALE_SONG"
ABYSSAL_BLOOM = "ABYSSAL_BLOOM"
GHOST_SHIP = "GHOST_SHIP"
SURFACE_STORM = "SURFACE_STORM"
OLD_SIGNAL = "OLD_SIGNAL"

ALL_EVENTS: tuple[str, ...] = (
    BLACK_CURRENT,
    WHALE_SONG,
    ABYSSAL_BLOOM,
    GHOST_SHIP,
    SURFACE_STORM,
    OLD_SIGNAL,
)


# Hard caps so events never spam the user.
MIN_INTER_EVENT_GAP: float = 60.0
DEFAULT_MIN_GAP: float = 180.0


@dataclass
class EventEffects:
    """Per-frame scalars an event exposes to the rest of the engine.

    The aquarium reads these every tick to bias spawn rates; the renderer
    reads ``tint`` / ``flicker`` / ``overlay_text`` to compose the frame.
    """

    name: str = ""
    banner: str = ""  # Big "BLACK CURRENT DETECTED" text shown briefly on start.
    overlay_text: str = ""  # Persistent small overlay while event is active.
    palette_tint: tuple[int, int, int] = (0, 0, 0)
    spawn_rate_mult: float = 1.0
    bubble_density_mult: float = 1.0
    rare_creature_mult: float = 1.0
    flicker: bool = False
    sound_cue: str = ""  # One-shot cue name; renderer consumes + clears.

    def reset(self) -> None:
        self.name = ""
        self.banner = ""
        self.overlay_text = ""
        self.palette_tint = (0, 0, 0)
        self.spawn_rate_mult = 1.0
        self.bubble_density_mult = 1.0
        self.rare_creature_mult = 1.0
        self.flicker = False
        self.sound_cue = ""


@dataclass
class Event:
    """Base class for events. Subclasses override ``on_*`` hooks."""

    name: str = ""
    duration: float = 20.0
    remaining: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.remaining = self.duration

    # Hooks. Default implementations are no-ops; subclasses set effects.
    def on_start(self, state: AquariumState) -> None: ...
    def on_tick(self, state: AquariumState, dt: float) -> None: ...
    def on_end(self, state: AquariumState) -> None:
        state.event_effects.reset()


# ---------------------------------------------------------------------------
# Concrete events
# ---------------------------------------------------------------------------


class BlackCurrentEvent(Event):
    def __init__(self) -> None:
        super().__init__(name=BLACK_CURRENT, duration=35.0)

    def on_start(self, state: AquariumState) -> None:
        e = state.event_effects
        e.name = self.name
        e.banner = "BLACK CURRENT DETECTED"
        e.overlay_text = ">> current: anomalous flow"
        e.palette_tint = (-25, -15, -10)
        e.spawn_rate_mult = 0.5
        e.rare_creature_mult = 2.0

    def on_tick(self, state: AquariumState, dt: float) -> None: ...


class WhaleSongEvent(Event):
    def __init__(self) -> None:
        super().__init__(name=WHALE_SONG, duration=25.0)

    def on_start(self, state: AquariumState) -> None:
        e = state.event_effects
        e.name = self.name
        e.banner = "WHALE SONG INTERCEPTED"
        e.overlay_text = ">> hydrophone :: deep song"
        e.palette_tint = (0, 5, 15)
        e.sound_cue = "whale_song"

    def on_tick(self, state: AquariumState, dt: float) -> None: ...


class AbyssalBloomEvent(Event):
    def __init__(self) -> None:
        super().__init__(name=ABYSSAL_BLOOM, duration=30.0)

    def on_start(self, state: AquariumState) -> None:
        e = state.event_effects
        e.name = self.name
        e.banner = "ABYSSAL BLOOM FORMING"
        e.overlay_text = ">> bioluminescence rising"
        e.palette_tint = (5, 30, 25)
        e.bubble_density_mult = 1.8


class GhostShipEvent(Event):
    def __init__(self) -> None:
        super().__init__(name=GHOST_SHIP, duration=30.0)

    def on_start(self, state: AquariumState) -> None:
        e = state.event_effects
        e.name = self.name
        e.banner = "GHOST SHIP PASSING"
        e.overlay_text = ">> radar return: phantom"
        e.palette_tint = (-15, -15, 5)
        e.flicker = True
        e.spawn_rate_mult = 0.6


class SurfaceStormEvent(Event):
    def __init__(self) -> None:
        super().__init__(name=SURFACE_STORM, duration=40.0)

    def on_start(self, state: AquariumState) -> None:
        e = state.event_effects
        e.name = self.name
        e.banner = "SURFACE STORM ABOVE"
        e.overlay_text = ">> swell: heavy"
        e.bubble_density_mult = 2.2
        e.palette_tint = (-10, -10, -10)


class OldSignalEvent(Event):
    def __init__(self) -> None:
        super().__init__(name=OLD_SIGNAL, duration=18.0)

    def on_start(self, state: AquariumState) -> None:
        e = state.event_effects
        e.name = self.name
        e.banner = "OLD SIGNAL RECEIVED"
        e.overlay_text = ">> SIGINT/PELAGIC/LOW"
        e.palette_tint = (-5, -10, 0)
        e.flicker = True
        e.sound_cue = "sonar_ping"


_EVENT_CLASSES: dict[str, type[Event]] = {
    BLACK_CURRENT: BlackCurrentEvent,
    WHALE_SONG: WhaleSongEvent,
    ABYSSAL_BLOOM: AbyssalBloomEvent,
    GHOST_SHIP: GhostShipEvent,
    SURFACE_STORM: SurfaceStormEvent,
    OLD_SIGNAL: OldSignalEvent,
}


def make_event(name: str) -> Event:
    """Instantiate an event by name. Raises ``KeyError`` on unknown names."""
    return _EVENT_CLASSES[name]()


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


@dataclass
class EventScheduler:
    """Drives event start/tick/end and enforces gap caps.

    Mood limits which events are eligible; the scheduler picks weighted-
    randomly among the eligible set when the cooldown elapses.
    """

    enabled: bool = True
    active: Event | None = None
    cooldown: float = DEFAULT_MIN_GAP
    min_gap: float = DEFAULT_MIN_GAP

    def tick(
        self,
        state: AquariumState,
        dt: float,
        rng: random.Random,
        allowed: frozenset[str],
    ) -> None:
        # Run the active event first; if it just expired, transition to idle.
        if self.active is not None:
            self.active.on_tick(state, dt)
            self.active.remaining -= dt
            if self.active.remaining <= 0:
                self.active.on_end(state)
                state.last_event_name = self.active.name
                self.active = None
                # Set a base cooldown before another event can fire.
                self.cooldown = max(MIN_INTER_EVENT_GAP, self.min_gap)
            return

        if not self.enabled:
            return
        self.cooldown -= dt
        if self.cooldown > 0:
            return

        candidates = [n for n in ALL_EVENTS if n in allowed]
        if not candidates:
            # No event allowed in current mood; check back soon.
            self.cooldown = MIN_INTER_EVENT_GAP
            return
        chosen = rng.choice(candidates)
        self.start(chosen, state)

    def start(self, name: str, state: AquariumState) -> Event:
        """Force-start an event by name. Used by ``--pin-event`` and tests."""
        evt = make_event(name)
        self.active = evt
        evt.on_start(state)
        return evt
