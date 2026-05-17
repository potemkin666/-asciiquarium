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


# ---------------------------------------------------------------------------
# Palette switching (ink-wash / sumi-e mode)
# ---------------------------------------------------------------------------

# Snapshots of the original colored palette so we can restore it on demand.
_DEFAULT_PALETTE: dict[str, RGB] = dict(PALETTE)
_DEFAULT_FG_DEFAULT: RGB = DEFAULT_FG
_BACKGROUND_DEFAULT: RGB = BACKGROUND

# Sumi-e ink-wash palette: warm off-white "paper" background and a small set
# of grayscale "ink" shades. Every color code is collapsed to one of these
# shades so the entire scene reads as a monochrome brush painting.
_INK_PAPER: RGB = (236, 228, 212)
_INK_SHADES: dict[str, RGB] = {
    "ink0": (40, 36, 34),  # darkest ink
    "ink1": (80, 74, 70),
    "ink2": (130, 122, 116),
    "ink3": (180, 170, 160),
}

# Map sprite color codes to ink shades. Bright codes -> lighter ink, plus
# black/blue stay near "ink0".
_INK_MAP: dict[str, str] = {
    "k": "ink0",
    "r": "ink1",
    "g": "ink2",
    "y": "ink2",
    "b": "ink0",
    "m": "ink1",
    "c": "ink2",
    "w": "ink3",
    "R": "ink1",
    "G": "ink2",
    "Y": "ink3",
    "B": "ink1",
    "M": "ink1",
    "C": "ink3",
    "W": "ink3",
}


def apply_palette(name: str) -> None:
    """Switch the global palette.

    Supported names: ``"default"`` (colorful) and ``"inkwash"`` (sumi-e).
    Mutates :data:`PALETTE`, :data:`DEFAULT_FG`, and :data:`BACKGROUND` in
    place so callers that look these up dynamically (engine/renderer) pick
    up the change without reloading the module.
    """
    global DEFAULT_FG, BACKGROUND
    PALETTE.clear()
    if name == "inkwash":
        for code, shade_key in _INK_MAP.items():
            PALETTE[code] = _INK_SHADES[shade_key]
        DEFAULT_FG = _INK_SHADES["ink0"]
        BACKGROUND = _INK_PAPER
    elif name == "default":
        PALETTE.update(_DEFAULT_PALETTE)
        DEFAULT_FG = _DEFAULT_FG_DEFAULT
        BACKGROUND = _BACKGROUND_DEFAULT
    else:
        # Unknown palette name: restore default and raise so misconfigured
        # CLIs fail loudly instead of silently rendering wrong colors.
        PALETTE.update(_DEFAULT_PALETTE)
        DEFAULT_FG = _DEFAULT_FG_DEFAULT
        BACKGROUND = _BACKGROUND_DEFAULT
        raise ValueError(f"unknown palette: {name!r}")
