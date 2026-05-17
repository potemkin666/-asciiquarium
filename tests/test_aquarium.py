from asciiquarium.aquarium import Aquarium


def test_aquarium_initial_population() -> None:
    aq = Aquarium(80, 30, seed=42)
    assert aq.scene.sprites_with_tag("waterline"), "waterline should be present"
    assert aq.scene.sprites_with_tag("castle"), "castle should be present"
    assert aq.scene.sprites_with_tag("seaweed"), "at least one seaweed strand"
    assert len(aq.scene.sprites_with_tag("fish")) >= 4


def test_aquarium_step_advances_time_and_keeps_population() -> None:
    aq = Aquarium(80, 30, seed=42)
    initial_fish = len(aq.scene.sprites_with_tag("fish"))
    # Run for a few simulated seconds.
    for _ in range(30):
        aq.step(0.1)
    # Fish population should remain roughly constant thanks to on_remove respawn.
    assert len(aq.scene.sprites_with_tag("fish")) >= initial_fish - 1
    assert aq.scene.time > 0


def test_aquarium_bubbles_eventually_spawn() -> None:
    aq = Aquarium(80, 30, seed=42)
    seen_bubble = False
    # Run enough simulated time for the spawner cooldown (0.5–1.5s) to fire at
    # least once. Bubbles rise quickly, so check every tick rather than only
    # at the end.
    for _ in range(60):
        aq.step(0.2)
        if aq.scene.sprites_with_tag("bubble"):
            seen_bubble = True
            break
    assert seen_bubble, "expected at least one bubble to spawn within ~12s of sim time"


def test_aquarium_reproducible_with_seed() -> None:
    a1 = Aquarium(80, 30, seed=123)
    a2 = Aquarium(80, 30, seed=123)
    fish1 = [(round(s.x, 3), s.y, s.vx) for s in a1.scene.sprites_with_tag("fish")]
    fish2 = [(round(s.x, 3), s.y, s.vx) for s in a2.scene.sprites_with_tag("fish")]
    assert fish1 == fish2
