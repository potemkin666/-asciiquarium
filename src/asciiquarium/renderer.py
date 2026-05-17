"""Pygame-based renderer and main loop.

Only this module imports pygame; the rest of the package is headless-testable.
"""

from __future__ import annotations

import os
import sys

import pygame

from .aquarium import Aquarium
from .colors import BACKGROUND, DEFAULT_FG
from .engine import Grid

DEFAULT_GRID_W = 132
DEFAULT_GRID_H = 40
DEFAULT_CELL_W = 9
DEFAULT_CELL_H = 16
TARGET_FPS = 20


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
            font.render("M", True, DEFAULT_FG)
            return font
        except Exception:
            continue
    return pygame.font.Font(None, max(10, cell_h))


def _measure_cell(font: pygame.font.Font) -> tuple[int, int]:
    surf = font.render("M", True, DEFAULT_FG)
    return surf.get_width(), surf.get_height()


class Renderer:
    """Owns the pygame window and draws :class:`Grid` instances."""

    def __init__(
        self,
        grid_w: int = DEFAULT_GRID_W,
        grid_h: int = DEFAULT_GRID_H,
        fullscreen: bool = False,
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
        # Pre-render a glyph cache (char + color -> Surface) to speed up draw.
        self._glyph_cache: dict = {}

        self._try_set_icon()

    # -- window management --------------------------------------------------

    def _window_size(self) -> tuple[int, int]:
        return self.grid_w * self.cell_w, self.grid_h * self.cell_h

    def _create_screen(self, fullscreen: bool) -> pygame.Surface:
        flags = pygame.FULLSCREEN if fullscreen else 0
        size = (0, 0) if fullscreen else self._window_size()
        return pygame.display.set_mode(size, flags)

    def toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        self.screen = self._create_screen(self._fullscreen)

    def _try_set_icon(self) -> None:
        path = _resource_path("assets", "icon.png")
        if os.path.exists(path):
            try:
                pygame.display.set_icon(pygame.image.load(path))
            except Exception:
                pass

    # -- drawing ------------------------------------------------------------

    def _glyph(self, ch: str, color: tuple[int, int, int]) -> pygame.Surface:
        key = (ch, color)
        surf = self._glyph_cache.get(key)
        if surf is None:
            surf = self.font.render(ch, True, color)
            self._glyph_cache[key] = surf
        return surf

    def draw(self, grid: Grid) -> None:
        screen = self.screen
        screen.fill(BACKGROUND)

        # Center the grid in the window if fullscreen made it larger.
        win_w, win_h = screen.get_size()
        grid_pix_w = self.grid_w * self.cell_w
        grid_pix_h = self.grid_h * self.cell_h
        ox = max(0, (win_w - grid_pix_w) // 2)
        oy = max(0, (win_h - grid_pix_h) // 2)

        cw, ch = self.cell_w, self.cell_h
        for y in range(self.grid_h):
            row_chars = grid.chars[y]
            row_colors = grid.colors[y]
            py = oy + y * ch
            for x in range(self.grid_w):
                glyph = row_chars[x]
                if glyph == " ":
                    continue
                surf = self._glyph(glyph, row_colors[x])
                screen.blit(surf, (ox + x * cw, py))

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
) -> int:
    renderer = Renderer(grid_w=grid_w, grid_h=grid_h, fullscreen=fullscreen)
    aquarium = Aquarium(grid_w, grid_h, seed=seed)
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
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        return 0
                    if event.key == pygame.K_p:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        aquarium = Aquarium(grid_w, grid_h, seed=seed)
                    elif event.key == pygame.K_f:
                        renderer.toggle_fullscreen()

            if not paused:
                aquarium.step(dt)

            aquarium.scene.render(grid)
            renderer.draw(grid)
    finally:
        renderer.shutdown()
