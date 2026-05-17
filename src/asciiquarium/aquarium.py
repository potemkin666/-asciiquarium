"""High-level aquarium scene: backgrounds, fish, bubbles and random events."""

from __future__ import annotations

import random
from dataclasses import dataclass

from . import sprites as art
from .engine import Scene, Sprite

# Depth layers (lower = drawn on top / closer to viewer)
DEPTH_WATERLINE = 100
DEPTH_CASTLE = 90
DEPTH_SEAWEED = 80
DEPTH_FISH = 50
DEPTH_BUBBLE = 40
DEPTH_BIG = 30
DEPTH_FOREGROUND = 10


# ---------------------------------------------------------------------------
# Background construction
# ---------------------------------------------------------------------------


def _build_waterline(width: int) -> str:
    """Tile :data:`art.WATERLINE_SEGMENTS` to ``width`` columns."""
    lines: list[str] = []
    for seg in art.WATERLINE_SEGMENTS:
        repeats = (width // len(seg)) + 1
        lines.append((seg * repeats)[:width])
    return "\n".join(lines)


def _waterline_mask(width: int, rows: int) -> str:
    return "\n".join(["C" * width for _ in range(rows)])


def add_background(scene: Scene) -> None:
    """Populate ``scene`` with non-moving backdrop sprites."""
    width = scene.width
    height = scene.height

    waterline_art = _build_waterline(width)
    waterline = Sprite(
        art=waterline_art,
        mask=_waterline_mask(width, len(art.WATERLINE_SEGMENTS)),
        x=0,
        y=5,
        depth=DEPTH_WATERLINE,
        tag="waterline",
    )
    scene.add(waterline)

    # Castle anchored to bottom-right
    castle = Sprite(
        art=art.CASTLE.art,
        mask=art.CASTLE.mask,
        depth=DEPTH_CASTLE,
        tag="castle",
    )
    castle.x = max(0, width - castle.width - 2)
    castle.y = max(0, height - castle.height)
    scene.add(castle)

    # Seaweed strands distributed along the floor
    rng = random.Random(0xC0FFEE)
    n_strands = max(3, width // 14)
    for i in range(n_strands):
        col = int((i + 0.5) * (width / n_strands)) + rng.randint(-2, 2)
        h = rng.randint(3, min(8, max(3, height // 4)))
        scene.add(_seaweed_sprite(col, height, h, phase=rng.random()))


def _seaweed_sprite(x: int, scene_height: int, length: int, phase: float) -> Sprite:
    """Build a single seaweed sprite of ``length`` segments anchored to the floor."""
    rows = []
    for i in range(length):
        rows.append(")" if (i + int(phase * 2)) % 2 == 0 else "(")
    art_str = "\n".join(rows)
    mask_str = "\n".join(["G"] * length)
    spr = Sprite(
        art=art_str,
        mask=mask_str,
        x=x,
        y=scene_height - length,
        depth=DEPTH_SEAWEED,
        tag="seaweed",
    )
    return spr


# ---------------------------------------------------------------------------
# Moving entities
# ---------------------------------------------------------------------------


@dataclass
class _Spawner:
    """Tracks cooldowns for random spawn events."""

    next_shark: float = 30.0
    next_whale: float = 45.0
    next_ship: float = 60.0
    next_big_fish: float = 90.0


def _pick_fish(rng: random.Random) -> art.DirectionalSprite:
    return rng.choice(art.FISH)


def add_fish(scene: Scene, rng: random.Random) -> Sprite:
    """Spawn one randomly-chosen fish moving across the screen."""
    fish_art = _pick_fish(rng)
    direction = rng.choice((-1, 1))
    chosen = fish_art.right if direction > 0 else fish_art.left
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=DEPTH_FISH + rng.randint(-5, 5),
        tag="fish",
    )
    speed = rng.uniform(4.0, 9.0)
    sprite.vx = speed * direction
    # Start just off-screen on the appropriate side.
    if direction > 0:
        sprite.x = -sprite.width
    else:
        sprite.x = scene.width
    # Underwater band (below waterline rows, above floor)
    waterline_h = len(art.WATERLINE_SEGMENTS) + 5  # offset for waterline depth
    floor = scene.height - 2
    band_top = waterline_h
    band_bottom = max(band_top + 1, floor - sprite.height)
    sprite.y = rng.randint(band_top, band_bottom)
    sprite.on_remove = _spawn_replacement_factory(scene, rng)
    scene.add(sprite)
    return sprite


def _spawn_replacement_factory(scene: Scene, rng: random.Random):
    def _cb(_old: Sprite) -> None:
        # Only replace if it was a generic fish (not one killed by shark, etc.)
        add_fish(scene, rng)

    return _cb


def add_bubble(scene: Scene, rng: random.Random, x: int, y: int) -> None:
    sprite = Sprite(
        art=".",
        mask="C",
        x=x,
        y=y,
        vy=-rng.uniform(3.0, 5.0),
        depth=DEPTH_BUBBLE,
        tag="bubble",
    )
    scene.add(sprite)


def add_shark(scene: Scene, rng: random.Random) -> Sprite:
    direction = rng.choice((-1, 1))
    chosen = art.SHARK.right if direction > 0 else art.SHARK.left
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=DEPTH_BIG,
        tag="shark",
    )
    sprite.vx = direction * rng.uniform(8.0, 12.0)
    if direction > 0:
        sprite.x = -sprite.width
    else:
        sprite.x = scene.width
    sprite.y = rng.randint(8, max(9, scene.height - sprite.height - 2))
    scene.add(sprite)
    return sprite


def add_whale(scene: Scene, rng: random.Random) -> Sprite:
    direction = rng.choice((-1, 1))
    chosen = art.WHALE.right if direction > 0 else art.WHALE.left
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=DEPTH_BIG,
        tag="whale",
    )
    sprite.vx = direction * rng.uniform(3.0, 5.0)
    if direction > 0:
        sprite.x = -sprite.width
    else:
        sprite.x = scene.width
    sprite.y = 6
    scene.add(sprite)
    return sprite


def add_ship(scene: Scene, rng: random.Random) -> Sprite:
    direction = rng.choice((-1, 1))
    chosen = art.SHIP.right if direction > 0 else art.SHIP.left
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=DEPTH_FOREGROUND,
        tag="ship",
    )
    sprite.vx = direction * rng.uniform(2.0, 4.0)
    if direction > 0:
        sprite.x = -sprite.width
    else:
        sprite.x = scene.width
    sprite.y = 0
    scene.add(sprite)
    return sprite


def add_big_fish(scene: Scene, rng: random.Random) -> Sprite:
    direction = rng.choice((-1, 1))
    chosen = art.BIG_FISH.right if direction > 0 else art.BIG_FISH.left
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=DEPTH_BIG + 1,
        tag="big_fish",
    )
    sprite.vx = direction * rng.uniform(3.0, 6.0)
    if direction > 0:
        sprite.x = -sprite.width
    else:
        sprite.x = scene.width
    sprite.y = rng.randint(10, max(11, scene.height - sprite.height - 2))
    scene.add(sprite)
    return sprite


# ---------------------------------------------------------------------------
# Aquarium driver
# ---------------------------------------------------------------------------


class Aquarium:
    """Top-level controller: owns the :class:`Scene` and spawns entities."""

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        self.scene = Scene(width, height)
        self.rng = random.Random(seed)
        self._spawner = _Spawner()
        self._bubble_cooldown = 0.0
        add_background(self.scene)
        n_fish = max(4, (width * height) // 350)
        for _ in range(n_fish):
            add_fish(self.scene, self.rng)

    @property
    def width(self) -> int:
        return self.scene.width

    @property
    def height(self) -> int:
        return self.scene.height

    def step(self, dt: float) -> None:
        self.scene.update(dt)
        self._maybe_spawn_bubbles(dt)
        self._maybe_spawn_random_events(dt)

    def _maybe_spawn_bubbles(self, dt: float) -> None:
        self._bubble_cooldown -= dt
        if self._bubble_cooldown > 0:
            return
        self._bubble_cooldown = self.rng.uniform(0.5, 1.5)
        # Emit a bubble at a random fish's mouth-ish location.
        fish = [s for s in self.scene.sprites if s.alive and s.tag == "fish"]
        if not fish:
            return
        chosen = self.rng.choice(fish)
        x = int(chosen.x + (chosen.width if chosen.vx > 0 else 0))
        y = int(chosen.y + chosen.height // 2)
        if 0 <= x < self.width and 0 <= y < self.height:
            add_bubble(self.scene, self.rng, x, y)

    def _maybe_spawn_random_events(self, dt: float) -> None:
        sp = self._spawner
        sp.next_shark -= dt
        sp.next_whale -= dt
        sp.next_ship -= dt
        sp.next_big_fish -= dt

        if sp.next_shark <= 0 and not self.scene.sprites_with_tag("shark"):
            add_shark(self.scene, self.rng)
            sp.next_shark = self.rng.uniform(30.0, 60.0)
        if sp.next_whale <= 0 and not self.scene.sprites_with_tag("whale"):
            add_whale(self.scene, self.rng)
            sp.next_whale = self.rng.uniform(45.0, 90.0)
        if sp.next_ship <= 0 and not self.scene.sprites_with_tag("ship"):
            add_ship(self.scene, self.rng)
            sp.next_ship = self.rng.uniform(60.0, 120.0)
        if sp.next_big_fish <= 0 and not self.scene.sprites_with_tag("big_fish"):
            add_big_fish(self.scene, self.rng)
            sp.next_big_fish = self.rng.uniform(60.0, 120.0)
