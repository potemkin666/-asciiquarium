"""Tests for palette switching (ink-wash / sumi-e mode)."""

from __future__ import annotations

from asciiquarium import colors


def test_apply_palette_inkwash_then_default_round_trip() -> None:
    default_palette = dict(colors.PALETTE)
    default_fg = colors.DEFAULT_FG
    default_bg = colors.BACKGROUND

    colors.apply_palette("inkwash")
    try:
        # Every color in ink-wash mode is a warm-tinted shade of ink:
        # r >= g >= b with small deltas (no saturated hues).
        for rgb in colors.PALETTE.values():
            r, g, b = rgb
            assert r >= g >= b, f"non-warm entry in ink-wash palette: {rgb}"
            assert (r - b) <= 25, f"too saturated for sumi-e: {rgb}"
        assert colors.BACKGROUND != default_bg
    finally:
        colors.apply_palette("default")

    assert colors.PALETTE == default_palette
    assert colors.DEFAULT_FG == default_fg
    assert colors.BACKGROUND == default_bg


def test_apply_palette_unknown_raises_and_restores_default() -> None:
    import pytest

    colors.apply_palette("default")  # ensure known starting state
    with pytest.raises(ValueError):
        colors.apply_palette("nope")
    # Defaults are still in place.
    assert colors.PALETTE["W"] == (255, 255, 255)


def test_color_for_uses_active_palette() -> None:
    colors.apply_palette("default")
    try:
        assert colors.color_for("W") == (255, 255, 255)
        colors.apply_palette("inkwash")
        rgb = colors.color_for("W")
        # Warm-tinted ink rather than a saturated color.
        assert rgb[0] >= rgb[1] >= rgb[2]
    finally:
        colors.apply_palette("default")
