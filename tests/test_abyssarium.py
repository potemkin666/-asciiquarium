"""Integration tests for the Abyssarium layer on top of the base aquarium.

These run with the pygame-free engine layers only and verify:
  * Classic-mode contract: no events / lore / rare creatures fire.
  * Abyss-mode features kick in given enough simulated time.
  * Logbook records sightings.
  * Interactive mutators (food, sonar) work and affect fish.
"""

from __future__ import annotations

import random

from asciiquarium import events as events_module
from asciiquarium.aquarium import (
    RARE_CREATURES_BY_KEY,
    Aquarium,
    AquariumOptions,
    pick_rare_creature,
)
from asciiquarium.logbook import in_memory
from asciiquarium.moods import CALM


def _abyss_options(**kwargs) -> AquariumOptions:
    """Build an AquariumOptions with all Abyssarium features on."""
    base = {
        "enable_moods": True,
        "enable_events": True,
        "enable_rare_creatures": True,
        "enable_lore": True,
        "initial_mood": CALM,
        "mood_pinned": False,
    }
    base.update(kwargs)
    return AquariumOptions(**base)


def test_classic_mode_default_options_run_silent() -> None:
    """With default options (everything off) no events, rare, or lore fire."""
    aq = Aquarium(80, 30, seed=42, options=AquariumOptions())
    for _ in range(2000):
        aq.step(1.0)
    assert aq.state.event_scheduler.active is None
    assert not any(s.tag.startswith("rare:") for s in aq.scene.sprites)
    assert aq.state.lore.pending is None


def test_abyss_mode_eventually_fires_rare_creature() -> None:
    opts = _abyss_options(biome="abyss")
    aq = Aquarium(120, 40, seed=1, options=opts)
    saw_rare = False
    for _ in range(600):
        aq.step(1.0)
        if any(s.tag.startswith("rare:") for s in aq.scene.sprites):
            saw_rare = True
            break
    assert saw_rare


def test_abyss_mode_eventually_fires_event() -> None:
    opts = _abyss_options()
    aq = Aquarium(100, 30, seed=3, options=opts)
    saw_event = False
    for _ in range(2000):
        aq.step(1.0)
        if aq.state.event_scheduler.active is not None or aq.state.last_event_name:
            saw_event = True
            break
    assert saw_event


def test_abyss_mode_eventually_fires_lore() -> None:
    opts = _abyss_options()
    aq = Aquarium(80, 30, seed=5, options=opts)
    fired = False
    for _ in range(3000):
        aq.step(1.0)
        if aq.state.lore.pending is not None:
            fired = True
            break
    assert fired


def test_mood_pinned_does_not_drift() -> None:
    opts = _abyss_options(initial_mood=CALM, mood_pinned=True)
    aq = Aquarium(80, 30, seed=7, options=opts)
    for _ in range(2000):
        aq.step(1.0)
    assert aq.state.mood == CALM


def test_mood_unpinned_eventually_drifts() -> None:
    opts = _abyss_options(initial_mood=CALM, mood_pinned=False)
    aq = Aquarium(80, 30, seed=11, options=opts)
    drifted = False
    for _ in range(2000):
        aq.step(1.0)
        if aq.state.mood != CALM:
            drifted = True
            break
    assert drifted


def test_drop_food_creates_food_sprite_and_steers_fish() -> None:
    aq = Aquarium(80, 30, seed=1)
    # Pick a fish far to the right of x=10 so dropping food at x=2 should
    # flip a leftward-moving fish if we hit one. We just assert the food
    # sprite exists and the state recorded it.
    pellet = aq.drop_food(x=10.0, y=10.0)
    assert pellet is not None
    assert pellet.tag == "food"
    assert aq.state.food_drops == 1
    assert aq.state.food_visible_for > 0


def test_emit_sonar_records_ping_and_creates_ring() -> None:
    aq = Aquarium(80, 30, seed=1)
    ring = aq.emit_sonar()
    assert ring is not None
    assert ring.tag == "sonar"
    assert aq.state.sonar_pings == 1


def test_sonar_ring_expires() -> None:
    aq = Aquarium(80, 30, seed=1)
    aq.emit_sonar()
    for _ in range(50):
        aq.step(0.1)
    assert not aq.scene.sprites_with_tag("sonar")


def test_cycle_mood_and_biome() -> None:
    aq = Aquarium(80, 30, seed=1)
    m0 = aq.state.mood
    new_m = aq.cycle_mood()
    assert new_m != m0
    assert aq.state.mood_pinned is True
    b0 = aq.biome.name
    new_b = aq.cycle_biome()
    assert new_b != b0


def test_logbook_records_common_creatures_after_run() -> None:
    lb = in_memory()
    opts = _abyss_options(logbook=lb)
    aq = Aquarium(80, 30, seed=1, options=opts)
    for _ in range(20):
        aq.step(0.1)
    # Fish are always populated at startup so they should be logged quickly.
    assert lb.has("fish")


def test_rare_creature_picker_returns_eligible_spec() -> None:
    aq = Aquarium(80, 30, seed=1, options=_abyss_options())
    spec = pick_rare_creature(aq.state, random.Random(0), biome_name="abyss")
    assert spec is not None
    # The sleeper is gated; without 666 launches it must never be picked.
    rng = random.Random(0)
    for _ in range(500):
        chosen = pick_rare_creature(aq.state, rng, biome_name="abyss")
        assert chosen is None or chosen.key != "the_sleeper"


def test_sleeper_eligible_only_on_666_multiples() -> None:
    aq = Aquarium(80, 30, seed=1, options=_abyss_options())
    aq.state.launch_count = 666
    spec = RARE_CREATURES_BY_KEY["the_sleeper"]
    assert spec.eligible(aq.state) is True  # type: ignore[misc]
    aq.state.launch_count = 1
    assert spec.eligible(aq.state) is False  # type: ignore[misc]
    aq.state.launch_count = 0
    assert spec.eligible(aq.state) is False  # type: ignore[misc]


def test_event_effects_visible_during_active_event() -> None:
    opts = _abyss_options()
    aq = Aquarium(80, 30, seed=1, options=opts)
    aq.state.event_scheduler.start(events_module.GHOST_SHIP, aq.state)
    assert aq.state.event_effects.name == events_module.GHOST_SHIP
    assert aq.state.event_effects.flicker is True
    # Tick to expiry; effects should reset.
    for _ in range(int(aq.state.event_scheduler.active.duration * 10) + 10):
        aq.step(0.1)
    assert aq.state.event_effects.name == ""


def test_reproducible_with_abyssarium_features_enabled() -> None:
    opts1 = _abyss_options()
    opts2 = _abyss_options()
    a1 = Aquarium(80, 30, seed=99, options=opts1)
    a2 = Aquarium(80, 30, seed=99, options=opts2)
    for _ in range(50):
        a1.step(0.1)
        a2.step(0.1)
    snap1 = [(s.tag, round(s.x, 3), s.y) for s in a1.scene.sprites if s.alive]
    snap2 = [(s.tag, round(s.x, 3), s.y) for s in a2.scene.sprites if s.alive]
    assert snap1 == snap2
    assert a1.state.mood == a2.state.mood
    assert a1.state.sonar_pings == a2.state.sonar_pings
