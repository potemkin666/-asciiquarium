"""High-level aquarium scene: backgrounds, fish, bubbles and random events."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field

from . import sprites as art
from .engine import Scene, Sprite

# Depth layers (lower = drawn on top / closer to viewer)
DEPTH_WATERLINE = 100
DEPTH_CASTLE = 90
DEPTH_SEAWEED = 80
DEPTH_TORII = 85
DEPTH_FISH = 50
DEPTH_BUBBLE = 40
DEPTH_BIG = 30
DEPTH_TURTLE = 35
DEPTH_SAKURA = 45
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


def add_background(
    scene: Scene,
    *,
    japanese: bool = False,
    seaweed_density: float = 1.0,
) -> None:
    """Populate ``scene`` with non-moving backdrop sprites.

    When ``japanese`` is true, a torii gate silhouette is anchored to the
    bottom-right corner (shifting the castle left to make room) and a
    bamboo shishi-odoshi is placed at the bottom-left of the floor.
    """
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

    # Torii gate silhouette (bottom-right) takes priority in japanese mode;
    # the castle is shifted left so it doesn't overlap.
    castle = Sprite(
        art=art.CASTLE.art,
        mask=art.CASTLE.mask,
        depth=DEPTH_CASTLE,
        tag="castle",
    )
    if japanese:
        torii = Sprite(
            art=art.TORII.art,
            mask=art.TORII.mask,
            depth=DEPTH_TORII,
            tag="torii",
        )
        torii.x = max(0, width - torii.width - 1)
        torii.y = max(0, height - torii.height)
        scene.add(torii)
        # Shift castle left of the torii so both fit.
        castle.x = max(0, width - castle.width - torii.width - 4)
        castle.y = max(0, height - castle.height)

        shishi = Sprite(
            art=art.SHISHI_ODOSHI_REST.art,
            mask=art.SHISHI_ODOSHI_REST.mask,
            depth=DEPTH_TORII,
            tag="shishi_odoshi",
        )
        shishi.x = 2
        shishi.y = max(0, height - shishi.height)
        scene.add(shishi)
    else:
        castle.x = max(0, width - castle.width - 2)
        castle.y = max(0, height - castle.height)
    scene.add(castle)

    # Seaweed strands distributed along the floor
    rng = random.Random(0xC0FFEE)
    base_strands = max(3, width // 14)
    n_strands = max(1, int(round(base_strands * max(0.0, seaweed_density))))
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
    # Turtles are deliberately rare and slow-moving.
    next_turtle: float = 120.0
    # Sakura petals (spring mode) fall as a steady drizzle.
    next_sakura: float = 0.5
    # Shishi-odoshi clack timer: fires every 30 seconds when enabled.
    next_clack: float = 30.0
    # Frame swap timer used to briefly show the tipped frame after a clack.
    shishi_tipped_for: float = 0.0


def _pick_fish(rng: random.Random, include_koi: bool = False) -> art.DirectionalSprite:
    pool: list[art.DirectionalSprite] = list(art.FISH)
    if include_koi:
        pool.extend(art.KOI)
    return rng.choice(pool)


def add_fish(scene: Scene, rng: random.Random, *, include_koi: bool = False) -> Sprite:
    """Spawn one randomly-chosen fish moving across the screen."""
    fish_art = _pick_fish(rng, include_koi=include_koi)
    direction = rng.choice((-1, 1))
    chosen = fish_art.right if direction > 0 else fish_art.left
    is_koi = fish_art in art.KOI
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=DEPTH_FISH + rng.randint(-5, 5),
        tag="koi" if is_koi else "fish",
    )
    # Koi are larger and a bit slower than the generic fish school.
    if is_koi:
        speed = rng.uniform(2.5, 5.0)
    else:
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
    sprite.on_remove = _spawn_replacement_factory(scene, rng, include_koi=include_koi)
    scene.add(sprite)
    return sprite


def _spawn_replacement_factory(scene: Scene, rng: random.Random, *, include_koi: bool = False):
    def _cb(_old: Sprite) -> None:
        # Only replace if it was a generic fish (not one killed by shark, etc.)
        add_fish(scene, rng, include_koi=include_koi)

    return _cb


def add_bubble(scene: Scene, rng: random.Random, x: int, y: int) -> None:
    # Bubbles rise and "pop" the moment they reach the waterline rather than
    # drifting silently off the top of the grid.
    waterline_top = 5  # y of the topmost waterline row (see add_background)
    sprite = Sprite(
        art=".",
        mask="C",
        x=x,
        y=y,
        vy=-rng.uniform(3.0, 5.0),
        depth=DEPTH_BUBBLE,
        tag="bubble",
        cull_policy="kill_above_y",
        cull_y=float(waterline_top + len(art.WATERLINE_SEGMENTS)),
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


def add_turtle(scene: Scene, rng: random.Random) -> Sprite:
    """Spawn a rare, slow-moving sea turtle drifting across the scene."""
    direction = rng.choice((-1, 1))
    chosen = art.TURTLE.right if direction > 0 else art.TURTLE.left
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=DEPTH_TURTLE,
        tag="turtle",
    )
    # Turtles glide along ~3x slower than the smallest fish.
    sprite.vx = direction * rng.uniform(1.0, 2.0)
    if direction > 0:
        sprite.x = -sprite.width
    else:
        sprite.x = scene.width
    # Prefer the lower half of the water column so turtles look like they
    # are gliding near the seabed rather than along the surface.
    mid = max(10, scene.height // 2)
    bottom = max(mid + 1, scene.height - sprite.height - 2)
    sprite.y = rng.randint(mid, bottom)
    scene.add(sprite)
    return sprite


def add_sakura_petal(scene: Scene, rng: random.Random) -> Sprite:
    """Spawn one cherry-blossom petal drifting down toward the waterline.

    Petals exist *above* the waterline (sky) and are culled by the
    :class:`Aquarium` driver once they reach the surface so they don't
    drift through the underwater band.
    """
    glyph = rng.choice(art.SAKURA_GLYPHS)
    code = rng.choice(art.SAKURA_COLOR_CODES)
    sprite = Sprite(
        art=glyph,
        mask=code,
        x=rng.randint(0, max(0, scene.width - 1)),
        y=0,
        vx=rng.uniform(-1.0, 1.0),
        vy=rng.uniform(1.0, 2.5),
        depth=DEPTH_SAKURA,
        tag="sakura",
        # Petals exist *above* the waterline and pop the moment they hit it.
        cull_policy="kill_below_y",
        cull_y=5.0,
    )
    scene.add(sprite)
    return sprite


# ---------------------------------------------------------------------------
# Aquarium driver
# ---------------------------------------------------------------------------


def _caustics_pattern(width: int, time: float) -> str:
    """Return one row of shifting ``~`` caustic ripples for the seabed.

    The pattern is a sparse cosine-modulated sequence of ``~`` and spaces
    so it looks like sunlight rippling across the sand. ``time`` shifts
    the pattern horizontally.
    """
    import math

    out = []
    for x in range(width):
        # Two overlapping sine waves at different frequencies make the
        # pattern look less periodic.
        v = math.sin((x * 0.35) - time * 2.0) + 0.6 * math.sin((x * 0.13) + time * 1.1)
        out.append("~" if v > 0.55 else " ")
    return "".join(out)


def _make_caustics_sprite(width: int, height: int) -> Sprite:
    """Create the caustic ripple sprite that lives just above the floor."""
    art_str = _caustics_pattern(width, 0.0)
    mask_str = "C" * width
    sprite = Sprite(
        art=art_str,
        mask=mask_str,
        x=0,
        y=max(0, height - 1),
        depth=DEPTH_FOREGROUND + 1,
        tag="caustics",
    )
    return sprite


# ---------------------------------------------------------------------------
# Biomes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BiomeSpec:
    """Tunable parameters for a biome preset."""

    name: str
    # Vertical gradient endpoints (top of grid -> bottom of grid).
    gradient_top: tuple[int, int, int]
    gradient_bottom: tuple[int, int, int]
    # Seaweed density multiplier (1.0 = default).
    seaweed_density: float = 1.0
    # Shark spawn cooldown multiplier (higher = rarer; ``inf`` disables).
    shark_cooldown_mult: float = 1.0


BIOMES: dict[str, BiomeSpec] = {
    "reef": BiomeSpec(
        name="reef",
        gradient_top=(40, 180, 200),
        gradient_bottom=(10, 60, 110),
        seaweed_density=1.3,
        shark_cooldown_mult=1.0,
    ),
    "abyss": BiomeSpec(
        name="abyss",
        gradient_top=(5, 10, 25),
        gradient_bottom=(0, 0, 0),
        seaweed_density=0.3,
        shark_cooldown_mult=0.8,
    ),
    "kelp-forest": BiomeSpec(
        name="kelp-forest",
        gradient_top=(20, 110, 90),
        gradient_bottom=(5, 40, 30),
        seaweed_density=2.5,
        shark_cooldown_mult=1.5,
    ),
    "arctic": BiomeSpec(
        name="arctic",
        gradient_top=(200, 230, 240),
        gradient_bottom=(40, 100, 150),
        seaweed_density=0.5,
        shark_cooldown_mult=float("inf"),  # no sharks in arctic preset
    ),
    "trench": BiomeSpec(
        name="trench",
        gradient_top=(2, 6, 18),
        gradient_bottom=(0, 0, 0),
        seaweed_density=0.2,
        shark_cooldown_mult=0.6,
    ),
    "default": BiomeSpec(
        name="default",
        gradient_top=(20, 80, 160),
        gradient_bottom=(0, 16, 48),
        seaweed_density=1.0,
        shark_cooldown_mult=1.0,
    ),
}


# ---------------------------------------------------------------------------
# Aquarium driver
# ---------------------------------------------------------------------------


@dataclass
class AquariumOptions:
    """Optional features controlled from the CLI."""

    japanese: bool = False
    spring: bool = False
    ink_wash: bool = False
    biome: str = "default"
    # Per-sprite subtle vertical bob for fish-like sprites.
    fish_bob: bool = True
    # Caustic ripples on the seabed row.
    caustics: bool = True
    # Audible terminal bell on shishi-odoshi clack (japanese mode).
    enable_bell: bool = True
    # File-like object used for the terminal bell; injectable for tests.
    bell_stream: object = field(default=None)


class Aquarium:
    """Top-level controller: owns the :class:`Scene` and spawns entities."""

    def __init__(
        self,
        width: int,
        height: int,
        seed: int | None = None,
        *,
        rng: random.Random | None = None,
        options: AquariumOptions | None = None,
    ) -> None:
        self.scene = Scene(width, height)
        # Cap total live sprite count so very large terminals don't accrete
        # unbounded particles. Derived from grid area (one sprite per ~40
        # cells), with a sensible floor so small grids still get traffic.
        self.scene.max_sprites = max(64, (width * height) // 40)
        self.options = options or AquariumOptions()
        self.rng = rng if rng is not None else random.Random(seed)
        self._spawner = _Spawner()
        self._bubble_cooldown = 0.0
        self.biome: BiomeSpec = BIOMES.get(self.options.biome, BIOMES["default"])
        # If the caller asked for an invalid biome name, surface that clearly.
        if self.options.biome not in BIOMES:
            raise ValueError(f"unknown biome: {self.options.biome!r} (choices: {sorted(BIOMES)})")
        add_background(
            self.scene,
            japanese=self.options.japanese,
            seaweed_density=self.biome.seaweed_density,
        )
        self._caustics: Sprite | None = None
        if self.options.caustics:
            self._caustics = _make_caustics_sprite(width, height)
            self.scene.add(self._caustics)
        # Koi join the regular fish pool when japanese mode is on.
        include_koi = self.options.japanese
        n_fish = max(4, (width * height) // 350)
        for _ in range(n_fish):
            spr = add_fish(self.scene, self.rng, include_koi=include_koi)
            if self.options.fish_bob and spr.tag in ("fish", "koi"):
                _enable_bob(spr, self.rng)

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
        self._update_caustics()
        if self.options.japanese and self.options.enable_bell:
            self._update_shishi_odoshi(dt)

    # -- helpers ------------------------------------------------------------

    def _update_caustics(self) -> None:
        if self._caustics is None or not self._caustics.alive:
            return
        new_art = _caustics_pattern(self.width, self.scene.time)
        # Mutate the cached art lines in place to avoid re-creating the
        # sprite each frame.
        self._caustics.art = new_art
        self._caustics._lines = [new_art]

    def _update_shishi_odoshi(self, dt: float) -> None:
        sp = self._spawner
        sp.next_clack -= dt
        if sp.shishi_tipped_for > 0:
            sp.shishi_tipped_for -= dt
            if sp.shishi_tipped_for <= 0:
                self._set_shishi_frame(art.SHISHI_ODOSHI_REST)
        if sp.next_clack <= 0:
            sp.next_clack = 30.0
            sp.shishi_tipped_for = 0.6
            self._set_shishi_frame(art.SHISHI_ODOSHI_TIPPED)
            self._ring_bell()

    def _set_shishi_frame(self, frame: art.SpriteArt) -> None:
        sprites = self.scene.sprites_with_tag("shishi_odoshi")
        if not sprites:
            return
        s = sprites[0]
        s.art = frame.art
        s.mask = frame.mask
        # Refresh cached split lines after mutating art/mask.
        from .engine import _split_lines  # local import to avoid cycle

        s._lines = _split_lines(frame.art)
        s._mask_lines = _split_lines(frame.mask) if frame.mask is not None else []

    def _ring_bell(self) -> None:
        stream = self.options.bell_stream if self.options.bell_stream is not None else sys.stdout
        try:
            stream.write("\a")
            flush = getattr(stream, "flush", None)
            if callable(flush):
                flush()
        except Exception:  # pragma: no cover - defensive
            pass

    def _maybe_spawn_bubbles(self, dt: float) -> None:
        self._bubble_cooldown -= dt
        if self._bubble_cooldown > 0:
            return
        self._bubble_cooldown = self.rng.uniform(0.5, 1.5)
        # Emit a bubble at a random fish-like sprite's mouth-ish location.
        fish = [s for s in self.scene.sprites if s.alive and s.tag in ("fish", "koi")]
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
        sp.next_turtle -= dt
        sp.next_sakura -= dt

        shark_mult = self.biome.shark_cooldown_mult
        if (
            shark_mult != float("inf")
            and sp.next_shark <= 0
            and not self.scene.sprites_with_tag("shark")
        ):
            add_shark(self.scene, self.rng)
            sp.next_shark = self.rng.uniform(30.0, 60.0) * shark_mult
        elif shark_mult == float("inf"):
            # Keep cooldown from going arbitrarily negative.
            sp.next_shark = 60.0
        if sp.next_whale <= 0 and not self.scene.sprites_with_tag("whale"):
            add_whale(self.scene, self.rng)
            sp.next_whale = self.rng.uniform(45.0, 90.0)
        if sp.next_ship <= 0 and not self.scene.sprites_with_tag("ship"):
            add_ship(self.scene, self.rng)
            sp.next_ship = self.rng.uniform(60.0, 120.0)
        if sp.next_big_fish <= 0 and not self.scene.sprites_with_tag("big_fish"):
            add_big_fish(self.scene, self.rng)
            sp.next_big_fish = self.rng.uniform(60.0, 120.0)
        if sp.next_turtle <= 0 and not self.scene.sprites_with_tag("turtle"):
            add_turtle(self.scene, self.rng)
            # Turtles are deliberately rare.
            sp.next_turtle = self.rng.uniform(120.0, 240.0)
        if self.options.spring and sp.next_sakura <= 0:
            add_sakura_petal(self.scene, self.rng)
            sp.next_sakura = self.rng.uniform(0.1, 0.5)


def _enable_bob(sprite: Sprite, rng: random.Random) -> None:
    """Enable subtle sinusoidal y-bob on a sprite."""
    sprite.bob_amplitude = 1.0
    sprite.bob_period = rng.uniform(2.0, 4.0)
    sprite.bob_phase = rng.uniform(0.0, 6.28318)
