"""Tests for the event system."""

from __future__ import annotations

import random

from asciiquarium import events
from asciiquarium.state import AquariumState


def _make_state(allowed: frozenset[str]) -> AquariumState:
    st = AquariumState(rng=random.Random(0))
    st.events_enabled = True
    st.event_scheduler.enabled = True
    return st


def test_all_event_classes_resolvable() -> None:
    for name in events.ALL_EVENTS:
        evt = events.make_event(name)
        assert evt.name == name
        assert evt.duration > 0


def test_event_lifecycle_start_tick_end() -> None:
    st = _make_state(frozenset(events.ALL_EVENTS))
    sched = st.event_scheduler
    evt = sched.start(events.WHALE_SONG, st)
    # on_start should have populated event_effects.
    assert st.event_effects.name == events.WHALE_SONG
    assert "WHALE SONG" in st.event_effects.banner
    # Tick to completion.
    remaining = evt.duration
    for _ in range(int(remaining * 10) + 5):
        sched.tick(st, 0.1, random.Random(0), frozenset(events.ALL_EVENTS))
    assert sched.active is None
    # on_end cleared effects.
    assert st.event_effects.name == ""
    assert st.last_event_name == events.WHALE_SONG


def test_scheduler_respects_allowed_set() -> None:
    """When no events are allowed, none start."""
    st = _make_state(frozenset())
    rng = random.Random(0)
    # Run for a long simulated time with empty allowed set.
    for _ in range(2000):
        st.event_scheduler.tick(st, 1.0, rng, frozenset())
    assert st.event_scheduler.active is None


def test_scheduler_eventually_starts_event_when_allowed() -> None:
    st = _make_state(frozenset({events.WHALE_SONG}))
    st.event_scheduler.cooldown = 0.0
    st.event_scheduler.min_gap = 60.0
    rng = random.Random(0)
    started = False
    for _ in range(100):
        st.event_scheduler.tick(st, 1.0, rng, frozenset({events.WHALE_SONG}))
        if st.event_scheduler.active is not None:
            started = True
            break
    assert started


def test_scheduler_enforces_min_inter_event_gap() -> None:
    """After one event ends, the next can't fire immediately."""
    st = _make_state(frozenset({events.OLD_SIGNAL}))
    rng = random.Random(0)
    st.event_scheduler.cooldown = 0.0
    st.event_scheduler.min_gap = 120.0
    # Force an event to start and end.
    evt = st.event_scheduler.start(events.OLD_SIGNAL, st)
    for _ in range(int(evt.duration * 10) + 5):
        st.event_scheduler.tick(st, 0.1, rng, frozenset({events.OLD_SIGNAL}))
    assert st.event_scheduler.active is None
    # The cooldown must now be >= MIN_INTER_EVENT_GAP.
    assert st.event_scheduler.cooldown >= events.MIN_INTER_EVENT_GAP


def test_unknown_event_name_raises() -> None:
    import pytest

    with pytest.raises(KeyError):
        events.make_event("NOT_AN_EVENT")
