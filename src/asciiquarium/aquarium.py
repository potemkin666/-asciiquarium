"""High-level aquarium scene: backgrounds, fish, bubbles and random events."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field

from . import sprites as art
from .engine import Scene, Sprite
from .events import EventScheduler  # re-exported for tests
from .logbook import Logbook, in_memory
from .moods import (
    CALM,
    get_mood,
    pick_next_mood,
)
from .state import AquariumState

__all__ = [
    "Aquarium",
    "AquariumOptions",
    "BIOMES",
    "BiomeSpec",
    "DEPTH_BIG",
    "DEPTH_BUBBLE",
    "DEPTH_CASTLE",
    "DEPTH_FISH",
    "DEPTH_FOREGROUND",
    "DEPTH_SAKURA",
    "DEPTH_SEAWEED",
    "DEPTH_TORII",
    "DEPTH_TURTLE",
    "DEPTH_WATERLINE",
    "EventScheduler",
    "add_background",
    "add_bubble",
    "add_big_fish",
    "add_fish",
    "add_rare_creature",
    "add_shark",
    "add_ship",
    "add_sakura_petal",
    "add_turtle",
    "add_whale",
]

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
DEPTH_RARE = 25  # rare creatures sit between BIG and FISH visually
DEPTH_FOOD = 38
DEPTH_SONAR = 8  # sonar ring is one of the topmost overlays


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
    # Rare-creature spawn cooldown (Abyssarium). Starts long; resets per-spawn.
    next_rare: float = 90.0


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
# Rare creatures (Abyssarium)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RareCreatureSpec:
    """Static description of a rare creature variant."""

    key: str  # logbook key
    sprite: art.DirectionalSprite
    base_weight: float
    speed_range: tuple[float, float]
    depth: int = DEPTH_RARE
    # Vertical band: 0.0 = top of underwater zone, 1.0 = floor.
    band_top: float = 0.2
    band_bottom: float = 0.9
    # Mood/biome biases: multiplied into ``base_weight`` when matching.
    mood_bias: tuple[str, ...] = ()
    biome_bias: tuple[str, ...] = ()
    # Optional gate: a callable returning True if this creature is eligible
    # given the current :class:`AquariumState`. Used by "The Sleeper".
    eligible: object = None  # type: ignore[assignment]


def _sleeper_eligible(state: AquariumState) -> bool:
    # Eligible only when launch_count is a multiple of 666 (1-in-666 across
    # launches, not 1-in-666 per second). The renderer bumps the counter at
    # startup.
    return state.launch_count > 0 and state.launch_count % 666 == 0


RARE_CREATURES: tuple[RareCreatureSpec, ...] = (
    RareCreatureSpec(
        key="giant_squid",
        sprite=art.GIANT_SQUID,
        base_weight=1.0,
        speed_range=(1.5, 2.5),
        band_top=0.5,
        band_bottom=0.85,
        mood_bias=("abyssal", "haunted"),
        biome_bias=("abyss", "trench"),
    ),
    RareCreatureSpec(
        key="ghost_whale",
        sprite=art.GHOST_WHALE,
        base_weight=1.0,
        speed_range=(2.0, 3.5),
        band_top=0.15,
        band_bottom=0.35,
        mood_bias=("haunted", "dreaming"),
    ),
    RareCreatureSpec(
        key="skeletal_coelacanth",
        sprite=art.SKELETAL_COELACANTH,
        base_weight=0.8,
        speed_range=(2.0, 3.0),
        band_top=0.45,
        band_bottom=0.8,
        mood_bias=("abyssal", "haunted"),
    ),
    RareCreatureSpec(
        key="deep_sea_angel",
        sprite=art.DEEP_SEA_ANGEL,
        base_weight=1.2,
        speed_range=(2.5, 4.0),
        band_top=0.35,
        band_bottom=0.7,
        mood_bias=("bioluminescent", "dreaming"),
    ),
    RareCreatureSpec(
        key="submarine_wreck",
        sprite=art.SUBMARINE_WRECK,
        base_weight=0.5,
        speed_range=(0.8, 1.4),
        depth=DEPTH_BIG + 2,
        band_top=0.65,
        band_bottom=0.9,
        mood_bias=("haunted", "polluted"),
    ),
    RareCreatureSpec(
        key="the_thing_below",
        sprite=art.THE_THING_BELOW,
        base_weight=0.3,
        speed_range=(0.6, 1.2),
        depth=DEPTH_BIG + 3,
        band_top=0.75,
        band_bottom=0.95,
        mood_bias=("abyssal", "haunted"),
        biome_bias=("abyss", "trench"),
    ),
    RareCreatureSpec(
        key="black_koi",
        sprite=art.BLACK_KOI,
        base_weight=0.8,
        speed_range=(2.5, 4.5),
        band_top=0.2,
        band_bottom=0.7,
        mood_bias=("haunted", "dreaming"),
    ),
    RareCreatureSpec(
        key="the_sleeper",
        sprite=art.THE_SLEEPER,
        base_weight=10.0,  # absurdly heavy — but gated by ``eligible``
        speed_range=(0.4, 0.8),
        depth=DEPTH_BIG + 5,
        band_top=0.55,
        band_bottom=0.9,
        eligible=_sleeper_eligible,
    ),
)

RARE_CREATURES_BY_KEY: dict[str, RareCreatureSpec] = {c.key: c for c in RARE_CREATURES}


def _weight_for(spec: RareCreatureSpec, state: AquariumState, biome_name: str) -> float:
    """Combined spawn weight given current mood/biome biases."""
    w = spec.base_weight
    if spec.mood_bias and state.mood in spec.mood_bias:
        w *= 2.5
    if spec.biome_bias and biome_name in spec.biome_bias:
        w *= 1.8
    # Sonar pings draw rare creatures from the dark.
    if state.sonar_pings > 0:
        w *= 1.0 + min(2.0, state.sonar_pings * 0.15)
    return max(0.0, w)


def pick_rare_creature(
    state: AquariumState,
    rng: random.Random,
    biome_name: str = "default",
) -> RareCreatureSpec | None:
    """Pick one eligible rare creature spec, or ``None`` if none qualifies."""
    eligible: list[tuple[RareCreatureSpec, float]] = []
    for spec in RARE_CREATURES:
        if spec.eligible is not None and not spec.eligible(state):  # type: ignore[misc]
            continue
        w = _weight_for(spec, state, biome_name)
        if w > 0:
            eligible.append((spec, w))
    if not eligible:
        return None
    total = sum(w for _, w in eligible)
    r = rng.random() * total
    acc = 0.0
    for spec, w in eligible:
        acc += w
        if r <= acc:
            return spec
    return eligible[-1][0]


def add_rare_creature(
    scene: Scene,
    rng: random.Random,
    spec: RareCreatureSpec,
) -> Sprite:
    """Spawn the rare creature described by ``spec`` and return its sprite."""
    direction = rng.choice((-1, 1))
    chosen = spec.sprite.right if direction > 0 else spec.sprite.left
    sprite = Sprite(
        art=chosen.art,
        mask=chosen.mask,
        depth=spec.depth,
        tag=f"rare:{spec.key}",
    )
    sprite.vx = direction * rng.uniform(*spec.speed_range)
    if direction > 0:
        sprite.x = -sprite.width
    else:
        sprite.x = scene.width
    # Convert (band_top, band_bottom) fractions into the underwater band.
    waterline_h = len(art.WATERLINE_SEGMENTS) + 5
    floor = max(waterline_h + 1, scene.height - 2)
    span = max(1, floor - waterline_h - sprite.height)
    y0 = waterline_h + int(span * spec.band_top)
    y1 = waterline_h + max(int(span * spec.band_bottom), int(span * spec.band_top) + 1)
    y1 = min(y1, max(waterline_h, floor - sprite.height))
    if y1 < y0:
        y0, y1 = y1, y0
    sprite.y = rng.randint(int(y0), int(y1))
    scene.add(sprite)
    return sprite


# ---------------------------------------------------------------------------
# Food / sonar entities
# ---------------------------------------------------------------------------


def add_food(scene: Scene, x: float, y: float) -> Sprite:
    """Drop a food pellet that sinks slowly."""
    sprite = Sprite(
        art="*",
        mask="Y",
        x=float(x),
        y=float(y),
        vy=2.0,
        depth=DEPTH_FOOD,
        tag="food",
        cull_policy="kill_below_y",
        cull_y=float(max(0, scene.height - 1)),
    )
    scene.add(sprite)
    return sprite


def add_sonar_ring(scene: Scene, x: float, y: float) -> Sprite:
    """Expanding sonar ring rendered as concentric `(` / `)` glyphs (~1.5s)."""
    sprite = Sprite(
        art="O",
        mask="C",
        x=float(x),
        y=float(y),
        depth=DEPTH_SONAR,
        tag="sonar",
    )
    # The ring uses a custom lifetime stored on the sprite via cull_y as
    # countdown seconds; we tick it in Aquarium._update_sonar.
    sprite.cull_y = 1.5
    sprite.cull_policy = "offscreen"
    return scene.add(sprite)


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
    # ---- Abyssarium feature toggles (default False so classic mode wins) ----
    enable_moods: bool = False
    enable_events: bool = False
    enable_rare_creatures: bool = False
    enable_lore: bool = False
    initial_mood: str = CALM
    mood_pinned: bool = True
    # Persistent launch count (passed in by CLI). Powers the "1-in-666" gate.
    launch_count: int = 0
    # Logbook (defaults to a no-disk one; CLI swaps in real one).
    logbook: Logbook | None = None


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

        # Build the central state. All Abyssarium-style behaviour is gated
        # by feature flags here so the legacy ("classic") code path is
        # bit-identical to before.
        self.state: AquariumState = AquariumState(rng=self.rng)
        self.state.mood = self.options.initial_mood
        self.state.mood_pinned = self.options.mood_pinned
        self.state.events_enabled = self.options.enable_events
        self.state.rare_creatures_enabled = self.options.enable_rare_creatures
        self.state.lore.enabled = self.options.enable_lore
        self.state.event_scheduler.enabled = self.options.enable_events
        self.state.launch_count = self.options.launch_count
        if self.options.logbook is not None:
            self.state.logbook = self.options.logbook
        else:
            self.state.logbook = in_memory()

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
        # ---- Abyssarium update hooks (no-ops unless enabled) ----
        self.state.sim_time += dt
        if self.options.enable_moods and not self.state.mood_pinned:
            self._update_mood(dt)
        if self.options.enable_events:
            self._update_events(dt)
        if self.options.enable_lore:
            self._update_lore(dt)
        if self.options.enable_rare_creatures:
            self._update_rare_creatures(dt)
        self._update_food_and_sonar(dt)
        # Track first-seen entries for the logbook.
        self._record_logbook_sightings()

    # -- Abyssarium helpers -------------------------------------------------

    def _update_mood(self, dt: float) -> None:
        st = self.state
        st.mood_clock -= dt
        if st.mood_clock > 0:
            return
        st.mood = pick_next_mood(st.mood, self.rng)
        st.mood_clock = st.mood_period

    def _update_events(self, dt: float) -> None:
        st = self.state
        mood = get_mood(st.mood)
        # If event running, just tick; otherwise consider starting one.
        st.event_scheduler.tick(st, dt, self.rng, mood.allowed_events)

    def _update_lore(self, dt: float) -> None:
        from .lore import tick as lore_tick

        st = self.state
        mood = get_mood(st.mood)
        lore_tick(st.lore, dt, self.rng, preferred_tags=mood.preferred_lore_tags)

    def _update_rare_creatures(self, dt: float) -> None:
        sp = self._spawner
        sp.next_rare -= dt
        if sp.next_rare > 0:
            return
        # Limit to one rare creature on-screen at a time to keep the
        # "you witnessed something" pacing intact.
        existing = [s for s in self.scene.sprites if s.alive and s.tag.startswith("rare:")]
        if existing:
            sp.next_rare = 30.0
            return
        mood_mult = get_mood(self.state.mood).rare_creature_mult
        event_mult = self.state.event_effects.rare_creature_mult
        combined_mult = max(0.1, mood_mult * event_mult)
        spec = pick_rare_creature(self.state, self.rng, biome_name=self.biome.name)
        if spec is None:
            sp.next_rare = 60.0
            return
        add_rare_creature(self.scene, self.rng, spec)
        # Cooldown: longer base when mood discourages rare creatures.
        base = self.rng.uniform(120.0, 240.0)
        sp.next_rare = base / combined_mult

    def _update_food_and_sonar(self, dt: float) -> None:
        st = self.state
        if st.food_visible_for > 0:
            st.food_visible_for = max(0.0, st.food_visible_for - dt)
        # Tick down sonar ring sprites; expand them slowly.
        for s in list(self.scene.sprites):
            if s.tag == "sonar" and s.alive:
                # Reuse cull_y as countdown timer (set by add_sonar_ring).
                s.cull_y -= dt
                if s.cull_y <= 0:
                    s.alive = False

    def _record_logbook_sightings(self) -> None:
        st = self.state
        # Common creatures
        for tag in ("fish", "turtle", "koi"):
            if self.scene.sprites_with_tag(tag):
                st.logbook.record(tag)
        # Rare creatures: tag is "rare:<key>"
        for s in self.scene.sprites:
            if s.alive and s.tag.startswith("rare:"):
                st.logbook.record(s.tag[len("rare:") :])
        # Events
        if st.event_scheduler.active is not None:
            st.logbook.record(st.event_scheduler.active.name)

    # -- food / sonar mutators (called from renderer) -----------------------

    def drop_food(self, x: float | None = None, y: float | None = None) -> Sprite | None:
        """Drop a food pellet; fish briefly steer toward it."""
        waterline_h = len(art.WATERLINE_SEGMENTS) + 5
        if x is None:
            x = self.rng.uniform(2, max(3, self.width - 3))
        if y is None:
            y = float(waterline_h)
        pellet = add_food(self.scene, x, y)
        self.state.record_food(x, y)
        # Steer fish toward the pellet for a few ticks.
        for s in self.scene.sprites:
            if s.tag in ("fish", "koi") and s.alive:
                dx = pellet.x - s.x
                if dx == 0:
                    continue
                desired = 1.0 if dx > 0 else -1.0
                # Flip direction if currently moving away.
                if (desired > 0 and s.vx < 0) or (desired < 0 and s.vx > 0):
                    s.vx = -s.vx
        return pellet

    def emit_sonar(self, x: float | None = None, y: float | None = None) -> Sprite | None:
        """Emit a sonar ping. Fish briefly scatter; rare creature weight rises."""
        if x is None:
            x = self.width / 2.0
        if y is None:
            y = self.height / 2.0
        ring = add_sonar_ring(self.scene, x, y)
        self.state.record_sonar()
        # Brief scatter: invert vx of fish near the ping centre.
        for s in self.scene.sprites:
            if s.tag in ("fish", "koi") and s.alive:
                # Flip the closer half so they appear to flee outward.
                if (s.x < x and s.vx > 0) or (s.x > x and s.vx < 0):
                    s.vx = -s.vx
        return ring

    def cycle_mood(self) -> str:
        from .moods import ALL_MOODS

        try:
            i = ALL_MOODS.index(self.state.mood)
        except ValueError:
            i = 0
        self.state.mood = ALL_MOODS[(i + 1) % len(ALL_MOODS)]
        self.state.mood_pinned = True
        return self.state.mood

    def cycle_biome(self) -> str:
        names = sorted(BIOMES.keys())
        try:
            i = names.index(self.biome.name)
        except ValueError:
            i = 0
        next_name = names[(i + 1) % len(names)]
        self.biome = BIOMES[next_name]
        return next_name

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
