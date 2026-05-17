"""ANSI-like color palette used by the renderer and sprite color masks.

Sprite art uses single-character color codes (matching the original
asciiquarium convention) to tint each glyph. This module maps those codes
to RGB tuples suitable for Pygame.

Color codes
-----------
=========  ===========
Code       Meaning
=========  ===========
``k``      black
``r``      red
``g``      green
``y``      yellow
``b``      blue
``m``      magenta
``c``      cyan
``w``      white / default
``R``      bright red
``G``      bright green
``Y``      bright yellow
``B``      bright blue
``M``      bright magenta
``C``      bright cyan
``W``      bright white
``.``      use default (white)
" "        (space) treated as default
=========  ===========
"""

from __future__ import annotations

RGB = tuple[int, int, int]

DEFAULT_FG: RGB = (220, 220, 220)
BACKGROUND: RGB = (0, 16, 48)  # deep ocean blue

PALETTE: dict[str, RGB] = {
    "k": (0, 0, 0),
    "r": (170, 0, 0),
    "g": (0, 170, 0),
    "y": (170, 170, 0),
    "b": (0, 0, 170),
    "m": (170, 0, 170),
    "c": (0, 170, 170),
    "w": (200, 200, 200),
    "R": (255, 85, 85),
    "G": (85, 255, 85),
    "Y": (255, 255, 85),
    "B": (85, 85, 255),
    "M": (255, 85, 255),
    "C": (85, 255, 255),
    "W": (255, 255, 255),
}


def color_for(code: str) -> RGB:
    """Return the RGB tuple for a sprite color-mask character.

    Unknown / blank codes fall back to :data:`DEFAULT_FG`.
    """
    if not code or code == " " or code == ".":
        return DEFAULT_FG
    return PALETTE.get(code, DEFAULT_FG)
