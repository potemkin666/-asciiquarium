"""Tests for new aquarium features added on top of the base scene."""

from __future__ import annotations

import io

from asciiquarium.aquarium import (
    BIOMES,
    Aquarium,
    AquariumOptions,
    _caustics_pattern,
    add_sakura_petal,
)
from asciiquarium.engine import Sprite


def test_default_options_match_base_behavior() -> None:
    aq = Aquarium(80, 30, seed=1)
    # No torii, no shishi-odoshi, no sakura by default.
    assert not aq.scene.sprites_with_tag("torii")
    assert not aq.scene.sprites_with_tag("shishi_odoshi")
    assert not aq.scene.sprites_with_tag("sakura")


def test_japanese_mode_adds_torii_and_shishi() -> None:
    aq = Aquarium(80, 30, seed=1, options=AquariumOptions(japanese=True))
    assert aq.scene.sprites_with_tag("torii"), "torii gate should be present"
    assert aq.scene.sprites_with_tag("shishi_odoshi"), "shishi-odoshi should be present"


def test_japanese_mode_koi_eventually_swim() -> None:
    aq = Aquarium(120, 40, seed=1, options=AquariumOptions(japanese=True))
    # Spawn many replacement fish so we very likely hit a koi from the
    # extended pool. Force-kill all initial fish to trigger respawns.
    for _ in range(50):
        for s in aq.scene.sprites_with_tag("fish") + aq.scene.sprites_with_tag("koi"):
            s.kill()
        aq.step(0.1)
    # At least one koi should have appeared across many spawns.
    assert any(s.tag == "koi" for s in aq.scene.sprites), "expected koi to spawn in japanese mode"


def test_spring_mode_spawns_sakura_petals() -> None:
    aq = Aquarium(80, 30, seed=1, options=AquariumOptions(spring=True))
    saw_petal = False
    for _ in range(30):
        aq.step(0.5)
        if aq.scene.sprites_with_tag("sakura"):
            saw_petal = True
            break
    assert saw_petal, "expected sakura petals to fall in spring mode"


def test_sakura_culled_at_waterline() -> None:
    aq = Aquarium(80, 30, seed=1, options=AquariumOptions(spring=True))
    petal = add_sakura_petal(aq.scene, aq.rng)
    petal.y = 10  # below waterline (waterline_top == 5)
    aq.step(0.01)
    assert not petal.alive, "petal past waterline should be culled"


def test_shishi_odoshi_clack_writes_bell_to_stream() -> None:
    buf = io.StringIO()
    aq = Aquarium(
        80,
        30,
        seed=1,
        options=AquariumOptions(japanese=True, enable_bell=True, bell_stream=buf),
    )
    # Default cooldown is 30s; one big tick should fire one clack.
    aq.step(31.0)
    assert "\a" in buf.getvalue(), "expected terminal bell on clack"


def test_shishi_odoshi_no_bell_when_disabled() -> None:
    buf = io.StringIO()
    aq = Aquarium(
        80,
        30,
        seed=1,
        options=AquariumOptions(japanese=True, enable_bell=False, bell_stream=buf),
    )
    aq.step(31.0)
    assert buf.getvalue() == ""


def test_caustics_sprite_present_by_default_and_pattern_shifts() -> None:
    aq = Aquarium(80, 30, seed=1)
    assert aq.scene.sprites_with_tag("caustics"), "caustics sprite should be added"
    a = _caustics_pattern(80, 0.0)
    b = _caustics_pattern(80, 1.0)
    assert a != b, "caustic pattern should shift with time"
    assert len(a) == 80


def test_caustics_can_be_disabled() -> None:
    aq = Aquarium(80, 30, seed=1, options=AquariumOptions(caustics=False))
    assert not aq.scene.sprites_with_tag("caustics")


def test_biome_unknown_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        Aquarium(80, 30, seed=1, options=AquariumOptions(biome="nope"))


def test_biome_arctic_has_no_sharks_after_long_run() -> None:
    aq = Aquarium(80, 30, seed=1, options=AquariumOptions(biome="arctic"))
    for _ in range(200):
        aq.step(1.0)
    assert not aq.scene.sprites_with_tag("shark"), "arctic biome should not spawn sharks"


def test_biome_specs_have_gradient_endpoints() -> None:
    for name, spec in BIOMES.items():
        assert len(spec.gradient_top) == 3 and len(spec.gradient_bottom) == 3, name
        assert all(0 <= c <= 255 for c in spec.gradient_top + spec.gradient_bottom)


def test_turtle_eventually_spawns_with_short_cooldown() -> None:
    aq = Aquarium(120, 40, seed=1)
    # Force the cooldown to be near-zero and step.
    aq._spawner.next_turtle = 0.0
    aq.step(0.01)
    assert aq.scene.sprites_with_tag("turtle"), "turtle should spawn when cooldown elapses"


def test_fish_bob_offsets_drawn_position_without_changing_y() -> None:
    """Per-sprite bob is a render-time effect: logical y unchanged."""
    s = Sprite(art="X", mask="W", x=0, y=10, bob_amplitude=2.0, bob_period=2.0)
    for _ in range(10):
        s.update(0.1)
    # Logical y is untouched.
    assert s.y == 10
    # Internal clock has advanced.
    assert s._bob_clock > 0


def test_aquarium_reproducible_with_seed_and_options() -> None:
    opts = AquariumOptions(japanese=True, spring=True, biome="reef")
    a1 = Aquarium(80, 30, seed=123, options=opts)
    a2 = Aquarium(80, 30, seed=123, options=opts)
    snap1 = [(s.tag, round(s.x, 3), s.y) for s in a1.scene.sprites]
    snap2 = [(s.tag, round(s.x, 3), s.y) for s in a2.scene.sprites]
    assert snap1 == snap2


def test_bubble_pops_at_waterline() -> None:
    """Bubbles use the kill_above_y policy and die at the waterline."""
    from asciiquarium import sprites as art
    from asciiquarium.aquarium import add_bubble

    aq = Aquarium(80, 30, seed=1)
    waterline_bottom = 5 + len(art.WATERLINE_SEGMENTS)
    # Spawn a bubble well below the waterline and let it rise.
    n_before = len(aq.scene.sprites_with_tag("bubble"))
    add_bubble(aq.scene, aq.rng, x=10, y=waterline_bottom + 3)
    bubble = aq.scene.sprites_with_tag("bubble")[n_before]
    assert bubble.cull_policy == "kill_above_y"
    assert bubble.cull_y == float(waterline_bottom)
    # Force-rise above the waterline and step once.
    bubble.y = waterline_bottom - 1.0
    aq.step(0.0001)
    assert not bubble.alive
    assert bubble not in aq.scene.sprites


def test_aquarium_default_sprite_cap_is_set() -> None:
    aq = Aquarium(80, 30, seed=1)
    assert aq.scene.max_sprites is not None
    assert aq.scene.max_sprites >= 64
    # Cap is derived from grid area.
    assert aq.scene.max_sprites == max(64, (80 * 30) // 40)


def test_aquarium_large_grid_cap_prevents_unbounded_particle_growth() -> None:
    aq = Aquarium(80, 30, seed=1)
    cap = aq.scene.max_sprites
    assert cap is not None
    # Force many bubble spawns; the cap should keep total live sprites bounded.
    from asciiquarium.aquarium import add_bubble

    for i in range(cap * 3):
        add_bubble(aq.scene, aq.rng, x=i % aq.width, y=aq.height - 2)
    live = [s for s in aq.scene.sprites if s.alive]
    assert len(live) <= cap
