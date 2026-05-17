"""Mode dispatcher.

Maps a single ``--mode`` choice (and the legacy mode flags it subsumes) to a
coherent preset of :class:`AquariumOptions` defaults *plus* the auxiliary
toggles that don't fit into :class:`AquariumOptions` (FPS hint, palette,
scanlines, lore visibility, etc.).

A mode is just data. CLI flags can still override individual fields after
resolution — modes are *defaults*, not commandments.

Pygame-free. The CLI parses arguments, calls :func:`resolve`, then hands
the resulting :class:`Preset` to the renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import moods as moods_module

CLASSIC = "classic"
ABYSS = "abyss"
JAPANESE = "japanese"
SPRING = "spring"
SUMI_E = "sumi-e"
NIGHTWATCH = "nightwatch"
SCREENSAVER = "screensaver"

ALL_MODES: tuple[str, ...] = (
    CLASSIC,
    ABYSS,
    JAPANESE,
    SPRING,
    SUMI_E,
    NIGHTWATCH,
    SCREENSAVER,
)


@dataclass
class Preset:
    """Concrete preset returned by :func:`resolve`. Fully self-describing."""

    mode: str = ABYSS
    # ``AquariumOptions`` knobs
    japanese: bool = False
    spring: bool = False
    ink_wash: bool = False
    biome: str = "default"
    fish_bob: bool = True
    caustics: bool = True
    enable_bell: bool = True
    # State knobs
    mood: str = moods_module.CALM
    mood_pinned: bool = False
    events_enabled: bool = True
    rare_creatures_enabled: bool = True
    lore_enabled: bool = True
    # Renderer-only knobs
    fps: int = 20
    fullscreen: bool = False
    crt_scanlines: bool = False
    sound_enabled: bool = False
    # Free-form notes, useful for debugging / future modes.
    tags: tuple[str, ...] = field(default_factory=tuple)


def resolve(mode: str = ABYSS) -> Preset:
    """Return a :class:`Preset` for the given mode name.

    ``classic`` strictly disables every "Abyssarium" feature so that
    long-time users see the original behaviour. ``abyss`` is the default
    cyber-ocean mutation.
    """
    if mode == CLASSIC:
        return Preset(
            mode=CLASSIC,
            mood=moods_module.CALM,
            mood_pinned=True,
            events_enabled=False,
            rare_creatures_enabled=False,
            lore_enabled=False,
            tags=("classic", "faithful"),
        )
    if mode == ABYSS:
        return Preset(
            mode=ABYSS,
            mood=moods_module.CALM,
            mood_pinned=False,
            events_enabled=True,
            rare_creatures_enabled=True,
            lore_enabled=True,
            tags=("abyssarium",),
        )
    if mode == JAPANESE:
        return Preset(
            mode=JAPANESE,
            japanese=True,
            mood=moods_module.CALM,
            mood_pinned=False,
            events_enabled=True,
            rare_creatures_enabled=True,
            lore_enabled=True,
            tags=("japanese",),
        )
    if mode == SPRING:
        return Preset(
            mode=SPRING,
            spring=True,
            mood=moods_module.FESTIVAL,
            mood_pinned=False,
            events_enabled=True,
            rare_creatures_enabled=True,
            lore_enabled=True,
            tags=("spring",),
        )
    if mode == SUMI_E:
        return Preset(
            mode=SUMI_E,
            ink_wash=True,
            japanese=True,
            mood=moods_module.DREAMING,
            mood_pinned=True,
            events_enabled=False,
            rare_creatures_enabled=False,
            lore_enabled=False,
            tags=("monochrome", "meditative"),
        )
    if mode == NIGHTWATCH:
        return Preset(
            mode=NIGHTWATCH,
            biome="abyss",
            mood=moods_module.ABYSSAL,
            mood_pinned=True,
            events_enabled=True,
            rare_creatures_enabled=True,
            lore_enabled=True,
            fps=10,
            crt_scanlines=True,
            enable_bell=False,
            tags=("nightwatch", "crt", "low_fps"),
        )
    if mode == SCREENSAVER:
        return Preset(
            mode=SCREENSAVER,
            mood=moods_module.CALM,
            mood_pinned=False,
            events_enabled=True,
            rare_creatures_enabled=True,
            lore_enabled=True,
            fullscreen=True,
            fps=20,
            tags=("screensaver", "fullscreen"),
        )
    raise ValueError(f"unknown mode: {mode!r} (choices: {ALL_MODES})")
