"""Core engine: sprites, frame grid, and scene manager.

This module is intentionally pygame-free so the simulation can be exercised
in headless unit tests. The :mod:`asciiquarium.renderer` module is the only
place that imports pygame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .colors import DEFAULT_FG, RGB, color_for

# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------


class Grid:
    """A fixed-size character + color frame buffer.

    Coordinates are ``(x, y)`` with the origin in the top-left. ``x``
    increases to the right, ``y`` increases downward.
    """

    __slots__ = ("width", "height", "chars", "colors")

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.clear()

    def clear(self) -> None:
        self.chars: list[list[str]] = [[" "] * self.width for _ in range(self.height)]
        self.colors: list[list[RGB]] = [[DEFAULT_FG] * self.width for _ in range(self.height)]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def put(self, x: int, y: int, ch: str, color: RGB) -> None:
        if self.in_bounds(x, y):
            self.chars[y][x] = ch
            self.colors[y][x] = color

    def get(self, x: int, y: int) -> str:
        if self.in_bounds(x, y):
            return self.chars[y][x]
        return " "


# ---------------------------------------------------------------------------
# Sprite
# ---------------------------------------------------------------------------


def _split_lines(art: str) -> list[str]:
    # Strip a single leading newline (so multi-line literals look nice).
    if art.startswith("\n"):
        art = art[1:]
    return art.splitlines()


@dataclass
class Sprite:
    """A multi-line ASCII art sprite with optional per-glyph color mask.

    Parameters
    ----------
    art:
        Multi-line ASCII art. Spaces are treated as transparent.
    mask:
        Optional same-shape color mask. Each character corresponds to a
        color code in :mod:`asciiquarium.colors`. If ``None``, the whole
        sprite is drawn in :data:`asciiquarium.colors.DEFAULT_FG`.
    x, y:
        Position of the sprite's top-left in the world grid (floats so
        sub-cell velocities work).
    vx, vy:
        Velocity in cells per second.
    depth:
        Draw order; lower depth is drawn on top (closer to the camera).
    transparent:
        Glyph treated as transparent (default: space).
    on_remove:
        Optional callback invoked when the sprite is despawned.
    tag:
        Free-form identifier used by the scene manager (e.g. ``"fish"``).
    """

    art: str
    mask: str | None = None
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    depth: int = 0
    transparent: str = " "
    on_remove: Callable[[Sprite], None] | None = None
    tag: str = ""
    alive: bool = True
    # Subtle sinusoidal y-axis "breathing" bob applied at draw time only.
    # Defaults to no bob; aquarium sets this for fish-like sprites.
    bob_amplitude: float = 0.0
    bob_period: float = 2.0
    bob_phase: float = 0.0
    _bob_clock: float = 0.0
    # Per-sprite lifecycle policy. Recognised values:
    #   "offscreen"     - kill when fully outside the grid (default; legacy behavior).
    #   "wrap_x"        - wrap horizontally; killed only if it leaves vertically.
    #   "kill_above_y"  - kill when ``y < cull_y`` (e.g. bubble crossing waterline).
    #   "kill_below_y"  - kill when ``y >= cull_y`` (e.g. petal crossing waterline).
    cull_policy: str = "offscreen"
    cull_y: float = 0.0

    _lines: list[str] = field(init=False, repr=False)
    _mask_lines: list[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._lines = _split_lines(self.art)
        if self.mask is not None:
            self._mask_lines = _split_lines(self.mask)
        else:
            self._mask_lines = []

    # -- geometry -----------------------------------------------------------

    @property
    def height(self) -> int:
        return len(self._lines)

    @property
    def width(self) -> int:
        return max((len(line) for line in self._lines), default=0)

    def bbox(self) -> tuple[int, int, int, int]:
        """Return integer ``(x0, y0, x1, y1)`` bounding box (exclusive)."""
        ix, iy = int(self.x), int(self.y)
        return ix, iy, ix + self.width, iy + self.height

    # -- simulation ---------------------------------------------------------

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.bob_amplitude:
            self._bob_clock += dt

    def is_offscreen(self, grid_w: int, grid_h: int, margin: int = 2) -> bool:
        x0, y0, x1, y1 = self.bbox()
        return x1 < -margin or y1 < -margin or x0 > grid_w + margin or y0 > grid_h + margin

    # -- rendering ----------------------------------------------------------

    def draw(self, grid: Grid) -> None:
        ix, iy = int(self.x), int(self.y)
        if self.bob_amplitude:
            import math

            offset = self.bob_amplitude * math.sin(
                (2.0 * math.pi * self._bob_clock / max(self.bob_period, 1e-6)) + self.bob_phase
            )
            iy += int(round(offset))
        for row, line in enumerate(self._lines):
            yy = iy + row
            mask_line = self._mask_lines[row] if row < len(self._mask_lines) else ""
            for col, ch in enumerate(line):
                if ch == self.transparent:
                    continue
                code = mask_line[col] if col < len(mask_line) else ""
                grid.put(ix + col, yy, ch, color_for(code))

    # -- helpers ------------------------------------------------------------

    def covers(self, x: int, y: int) -> bool:
        """True if the sprite has a non-transparent glyph at world ``(x, y)``."""
        ix, iy = int(self.x), int(self.y)
        row = y - iy
        col = x - ix
        if row < 0 or row >= len(self._lines):
            return False
        line = self._lines[row]
        if col < 0 or col >= len(line):
            return False
        return line[col] != self.transparent

    def kill(self) -> None:
        self.alive = False


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------


# Tags that should never be evicted to make room for new spawns. Aquarium can
# override the per-scene set; this default protects long-lived decor and the
# primary fish school.
DEFAULT_PROTECTED_TAGS: frozenset[str] = frozenset(
    {
        "waterline",
        "castle",
        "seaweed",
        "torii",
        "shishi_odoshi",
        "caustics",
        "fish",
        "koi",
    }
)


class Scene:
    """Holds all sprites and advances the simulation by fixed time steps."""

    def __init__(
        self,
        width: int,
        height: int,
        *,
        max_sprites: int | None = None,
        protected_tags: frozenset[str] | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.sprites: list[Sprite] = []
        self.time: float = 0.0
        self.max_sprites: int | None = max_sprites
        self.protected_tags: frozenset[str] = (
            protected_tags if protected_tags is not None else DEFAULT_PROTECTED_TAGS
        )

    # -- sprite management --------------------------------------------------

    def add(self, sprite: Sprite) -> Sprite:
        # Enforce a global cap on live sprite count by evicting the oldest
        # non-protected sprite. If no eviction candidate exists and the new
        # sprite itself is unprotected, refuse the add (caller's reference
        # still works but the sprite never enters the scene).
        if self.max_sprites is not None:
            live = [s for s in self.sprites if s.alive]
            if len(live) >= self.max_sprites:
                victim: Sprite | None = None
                for s in self.sprites:
                    if s.alive and s.tag not in self.protected_tags:
                        victim = s
                        break
                if victim is not None:
                    victim.alive = False
                elif sprite.tag not in self.protected_tags:
                    # No room and the newcomer isn't protected: drop it.
                    sprite.alive = False
                    return sprite
                # If newcomer is protected and no victim was found, allow the
                # cap to be (transiently) exceeded rather than evict decor.
        self.sprites.append(sprite)
        return sprite

    def remove(self, sprite: Sprite) -> None:
        sprite.alive = False

    def sprites_with_tag(self, tag: str) -> list[Sprite]:
        return [s for s in self.sprites if s.alive and s.tag == tag]

    # -- step ---------------------------------------------------------------

    def _should_cull(self, s: Sprite) -> bool:
        policy = s.cull_policy
        if policy == "wrap_x":
            # Wrap horizontally; only cull if it leaves vertically.
            x0, y0, x1, y1 = s.bbox()
            if y1 < -2 or y0 > self.height + 2:
                return True
            if x0 > self.width:
                s.x = -s.width
            elif x1 < 0:
                s.x = float(self.width)
            return False
        if policy == "kill_above_y":
            return s.y < s.cull_y
        if policy == "kill_below_y":
            return s.y >= s.cull_y
        # Default / "offscreen".
        return s.is_offscreen(self.width, self.height)

    def update(self, dt: float) -> None:
        self.time += dt
        for s in self.sprites:
            if s.alive:
                s.update(dt)
        # Cull dead or policy-expired sprites.
        survivors: list[Sprite] = []
        for s in self.sprites:
            if not s.alive or self._should_cull(s):
                if s.on_remove is not None:
                    try:
                        s.on_remove(s)
                    except Exception:  # pragma: no cover - defensive
                        pass
                s.alive = False
                continue
            survivors.append(s)
        self.sprites = survivors

    # -- render -------------------------------------------------------------

    def render(self, grid: Grid) -> None:
        grid.clear()
        # Higher depth drawn first so lower depth ends up on top.
        for s in sorted(self.sprites, key=lambda s: -s.depth):
            if s.alive:
                s.draw(grid)
