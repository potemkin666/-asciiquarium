"""Pygame-based renderer and main loop.

Only this module imports pygame; the rest of the package is headless-testable.
"""

from __future__ import annotations

import os
import string
import sys

import pygame

from . import colors
from .aquarium import BIOMES, Aquarium, AquariumOptions
from .engine import Grid

DEFAULT_GRID_W = 132
DEFAULT_GRID_H = 40
DEFAULT_CELL_W = 9
DEFAULT_CELL_H = 16
TARGET_FPS = 20

# Glyphs we pre-render at startup. ``string.printable`` minus whitespace
# (we don't draw spaces) plus the small set of non-ASCII block / brush
# characters used by ink-wash and seabed sprites.
_EXTRA_GLYPHS = "░▒▓~"


def _resource_path(*parts: str) -> str:
    """Resolve a packaged resource path (works under PyInstaller too)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "asciiquarium", *parts)
    return os.path.join(os.path.dirname(__file__), *parts)


def _load_font(cell_h: int) -> pygame.font.Font:
    """Pick a monospaced font of an appropriate size.

    ``pygame.font.SysFont`` always returns a Font object: if it cannot find
    the requested family it falls back to the built-in default font. We try
    a few common monospaced names and verify the returned font can actually
    render a glyph before accepting it.
    """
    candidates = ["dejavusansmono", "menlo", "consolas", "couriernew", "monospace"]
    size = max(8, cell_h - 2)
    for name in candidates:
        try:
            font = pygame.font.SysFont(name, size)
            # Sanity-check that the font can render a glyph.
            font.render("M", True, colors.DEFAULT_FG)
            return font
        except Exception:
            continue
    return pygame.font.Font(None, max(10, cell_h))


def _measure_cell(font: pygame.font.Font) -> tuple[int, int]:
    surf = font.render("M", True, colors.DEFAULT_FG)
    return surf.get_width(), surf.get_height()


def _printable_glyphs() -> list[str]:
    """ASCII printable glyphs minus whitespace, plus a handful of block chars."""
    drawable = "".join(ch for ch in string.printable if not ch.isspace())
    return list(drawable) + list(_EXTRA_GLYPHS)


def _palette_colors() -> list[tuple[int, int, int]]:
    """All RGB colors currently in use by the palette plus the default fg."""
    seen: list[tuple[int, int, int]] = []
    for rgb in list(colors.PALETTE.values()) + [colors.DEFAULT_FG]:
        if rgb not in seen:
            seen.append(rgb)
    return seen


def _build_gradient(width: int, height: int, top: tuple, bottom: tuple) -> pygame.Surface:
    """Build a vertical gradient surface from ``top`` (y=0) to ``bottom`` (y=height-1)."""
    surf = pygame.Surface((width, height))
    if height <= 1:
        surf.fill(top)
        return surf
    for y in range(height):
        t = y / (height - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (width - 1, y))
    return surf


class Renderer:
    """Owns the pygame window and draws :class:`Grid` instances."""

    def __init__(
        self,
        grid_w: int = DEFAULT_GRID_W,
        grid_h: int = DEFAULT_GRID_H,
        fullscreen: bool = False,
        *,
        gradient_top: tuple[int, int, int] | None = None,
        gradient_bottom: tuple[int, int, int] | None = None,
    ) -> None:
        pygame.init()
        pygame.display.set_caption("asciiquarium")

        self.grid_w = grid_w
        self.grid_h = grid_h

        self.font = _load_font(DEFAULT_CELL_H)
        cw, ch = _measure_cell(self.font)
        self.cell_w = max(1, cw)
        self.cell_h = max(1, ch)

        self._fullscreen = fullscreen
        self.screen = self._create_screen(fullscreen)
        # The grid is composited to this off-screen canvas, then the canvas
        # is blit once to the display. Avoids many tiny blits hitting the
        # window surface every frame.
        self._canvas: pygame.Surface = pygame.Surface(self._grid_pixel_size())
        # Bounded glyph cache: pre-populated once with every printable glyph
        # in every palette color. Subsequent lookups are O(1) dict hits and
        # the dict never grows during rendering.
        self._glyph_cache: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}
        self._prime_glyph_cache()
        self._gradient_top = gradient_top
        self._gradient_bottom = gradient_bottom
        self._gradient_surface: pygame.Surface | None = None
        self._rebuild_gradient()

        self._try_set_icon()

    # -- window management --------------------------------------------------

    def _grid_pixel_size(self) -> tuple[int, int]:
        return self.grid_w * self.cell_w, self.grid_h * self.cell_h

    def _window_size(self) -> tuple[int, int]:
        return self._grid_pixel_size()

    def _create_screen(self, fullscreen: bool) -> pygame.Surface:
        if fullscreen:
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        return pygame.display.set_mode(self._window_size(), pygame.RESIZABLE)

    def toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        self.screen = self._create_screen(self._fullscreen)

    def handle_resize(self, w: int, h: int) -> None:
        """Respond to a window resize: keep the grid size, recreate the screen.

        The off-screen canvas is unchanged (grid pixel size is fixed). The
        ``draw`` method already centers the canvas inside the window.
        """
        if self._fullscreen:
            return
        w = max(self.cell_w, w)
        h = max(self.cell_h, h)
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)

    def _try_set_icon(self) -> None:
        path = _resource_path("assets", "icon.png")
        if os.path.exists(path):
            try:
                pygame.display.set_icon(pygame.image.load(path))
            except Exception:
                pass

    # -- glyph cache --------------------------------------------------------

    def _prime_glyph_cache(self) -> None:
        """Pre-render every printable glyph in every palette color.

        The cache size is bounded by ``|glyphs| * |colors|`` and is built
        once at startup, so per-frame draw never allocates a Surface.
        """
        self._glyph_cache.clear()
        for ch in _printable_glyphs():
            for color in _palette_colors():
                self._glyph_cache[(ch, color)] = self.font.render(ch, True, color)

    def refresh_palette(self) -> None:
        """Rebuild caches that depend on the active color palette.

        Call after :func:`asciiquarium.colors.apply_palette`.
        """
        self._prime_glyph_cache()
        self._rebuild_gradient()

    def _rebuild_gradient(self) -> None:
        if self._gradient_top is None or self._gradient_bottom is None:
            self._gradient_surface = None
            return
        self._gradient_surface = _build_gradient(
            *self._grid_pixel_size(),
            self._gradient_top,
            self._gradient_bottom,
        )

    # -- drawing ------------------------------------------------------------

    def _glyph(self, ch: str, color: tuple[int, int, int]) -> pygame.Surface:
        key = (ch, color)
        surf = self._glyph_cache.get(key)
        if surf is None:
            # Glyph or color not in the pre-cache (e.g. a sprite uses an
            # unusual non-ASCII char). Render once and stash it.
            surf = self.font.render(ch, True, color)
            self._glyph_cache[key] = surf
        return surf

    def draw(self, grid: Grid) -> None:
        canvas = self._canvas
        # Background: vertical gradient if configured, else flat color.
        if self._gradient_surface is not None:
            canvas.blit(self._gradient_surface, (0, 0))
        else:
            canvas.fill(colors.BACKGROUND)

        cw, ch = self.cell_w, self.cell_h
        for y in range(self.grid_h):
            row_chars = grid.chars[y]
            row_colors = grid.colors[y]
            py = y * ch
            for x in range(self.grid_w):
                glyph = row_chars[x]
                if glyph == " ":
                    continue
                surf = self._glyph(glyph, row_colors[x])
                canvas.blit(surf, (x * cw, py))

        # One blit from canvas to the (possibly resized) display surface.
        screen = self.screen
        screen.fill(colors.BACKGROUND)
        win_w, win_h = screen.get_size()
        cw_total, ch_total = self._grid_pixel_size()
        ox = max(0, (win_w - cw_total) // 2)
        oy = max(0, (win_h - ch_total) // 2)
        screen.blit(canvas, (ox, oy))

        pygame.display.flip()

    def shutdown(self) -> None:
        pygame.quit()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run(
    grid_w: int = DEFAULT_GRID_W,
    grid_h: int = DEFAULT_GRID_H,
    fps: int = TARGET_FPS,
    seed: int | None = None,
    fullscreen: bool = False,
    *,
    options: AquariumOptions | None = None,
    rng=None,
) -> int:
    options = options or AquariumOptions()
    biome = BIOMES.get(options.biome)
    gradient_top = biome.gradient_top if biome is not None else None
    gradient_bottom = biome.gradient_bottom if biome is not None else None

    renderer = Renderer(
        grid_w=grid_w,
        grid_h=grid_h,
        fullscreen=fullscreen,
        gradient_top=gradient_top,
        gradient_bottom=gradient_bottom,
    )
    aquarium = Aquarium(grid_w, grid_h, seed=seed, rng=rng, options=options)
    grid = Grid(grid_w, grid_h)
    clock = pygame.time.Clock()
    paused = False

    try:
        while True:
            dt_ms = clock.tick(fps)
            dt = dt_ms / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 0
                if event.type == pygame.VIDEORESIZE:
                    renderer.handle_resize(event.w, event.h)
                    continue
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        return 0
                    if event.key == pygame.K_p:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        aquarium = Aquarium(grid_w, grid_h, seed=seed, options=options)
                    elif event.key == pygame.K_f:
                        renderer.toggle_fullscreen()

            if not paused:
                aquarium.step(dt)

            aquarium.scene.render(grid)
            renderer.draw(grid)
    finally:
        renderer.shutdown()
