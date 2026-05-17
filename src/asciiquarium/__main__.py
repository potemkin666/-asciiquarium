"""Command-line entry point for ``python -m asciiquarium`` and console scripts."""

from __future__ import annotations

import argparse
import sys

from .aquarium import BIOMES, AquariumOptions
from .colors import apply_palette
from .logbook import Logbook
from .modes import ABYSS, ALL_MODES, CLASSIC, JAPANESE, NIGHTWATCH, SCREENSAVER, SPRING, SUMI_E
from .modes import resolve as resolve_mode
from .moods import ALL_MOODS, is_valid_mood
from .paths import bump_launch_counter, logbook_path
from .qrng import make_rng
from .seedcode import SeedCode
from .seedcode import parse as parse_code
from .version import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asciiquarium",
        description="A self-contained ASCII aquarium animation (Pygame).",
    )
    parser.add_argument("--width", type=int, default=132, help="grid width in cells (default: 132)")
    parser.add_argument("--height", type=int, default=40, help="grid height in cells (default: 40)")
    parser.add_argument("--fps", type=int, default=None, help="frames per second (default: 20)")
    parser.add_argument(
        "--seed", type=int, default=None, help="random seed for reproducible scenes"
    )
    parser.add_argument(
        "--quantum-seed",
        action="store_true",
        help="seed the RNG from ANU's quantum RNG service (falls back to OS entropy)",
    )
    parser.add_argument("--fullscreen", action="store_true", help="launch in fullscreen mode")
    parser.add_argument(
        "--biome",
        choices=sorted(BIOMES.keys()),
        default=None,
        help="biome preset (gradient + density tweaks)",
    )
    parser.add_argument(
        "--mode",
        choices=list(ALL_MODES),
        default=ABYSS,
        help="atmospheric preset (default: abyss; use --classic for nostalgic mode)",
    )
    # Convenience flags equivalent to ``--mode <name>``.
    parser.add_argument(
        "--classic", action="store_true", help="alias for --mode classic (faithful original)"
    )
    parser.add_argument("--abyss", action="store_true", help="alias for --mode abyss")
    parser.add_argument("--nightwatch", action="store_true", help="alias for --mode nightwatch")
    parser.add_argument("--screensaver", action="store_true", help="alias for --mode screensaver")
    parser.add_argument(
        "--japanese",
        action="store_true",
        help="enable Japanese-themed scene: torii gate, shishi-odoshi, koi (錦鯉)",
    )
    parser.add_argument(
        "--spring",
        action="store_true",
        help="drift sakura petals down to the waterline",
    )
    parser.add_argument(
        "--ink-wash",
        action="store_true",
        help="monochrome sumi-e palette using ░▒▓ shading",
    )
    parser.add_argument(
        "--no-bob",
        action="store_true",
        help="disable subtle per-sprite vertical bob",
    )
    parser.add_argument(
        "--no-caustics",
        action="store_true",
        help="disable caustic ripple effect on the seabed",
    )
    parser.add_argument(
        "--no-bell",
        action="store_true",
        help="suppress audible terminal bell on shishi-odoshi clack",
    )
    parser.add_argument(
        "--mood",
        choices=list(ALL_MOODS),
        default=None,
        help="pin a specific mood for this session",
    )
    parser.add_argument("--no-events", action="store_true", help="disable atmospheric events")
    parser.add_argument("--no-lore", action="store_true", help="disable lore fragments")
    parser.add_argument("--no-rare", action="store_true", help="disable rare creature spawns")
    parser.add_argument(
        "--code",
        default=None,
        help="tank seed code of the form BIOME-SEED-MOOD[-MOD], overrides --biome/--seed/--mood",
    )
    parser.add_argument(
        "--print-code",
        action="store_true",
        help="print the resolved tank seed code and exit",
    )
    parser.add_argument(
        "--no-logbook",
        action="store_true",
        help="do not persist the local logbook to disk",
    )
    parser.add_argument("--version", action="version", version=f"asciiquarium {__version__}")
    return parser


def _resolve_mode_name(args: argparse.Namespace) -> str:
    # Convenience alias flags override --mode in order of specificity.
    if args.classic:
        return CLASSIC
    if args.nightwatch:
        return NIGHTWATCH
    if args.screensaver:
        return SCREENSAVER
    if args.abyss:
        return ABYSS
    # Legacy flags upgrade to their dedicated modes if no --mode given.
    if args.mode == ABYSS:
        if args.japanese and args.spring and args.ink_wash:
            return SUMI_E
        if args.ink_wash:
            return SUMI_E
        if args.japanese:
            return JAPANESE
        if args.spring:
            return SPRING
    return args.mode


def _apply_code_to_args(args: argparse.Namespace, code: SeedCode) -> None:
    args.biome = code.biome
    args.seed = code.seed
    args.mood = code.mood
    if code.modifier == "KOI":
        args.japanese = True
    elif code.modifier == "SUMI":
        args.ink_wash = True
        args.japanese = True
    elif code.modifier == "SPRING":
        args.spring = True
    elif code.modifier == "NIGHTWATCH":
        args.nightwatch = True


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.code:
        try:
            code = parse_code(args.code)
        except ValueError as exc:
            print(f"error: invalid --code: {exc}", file=sys.stderr)
            return 2
        _apply_code_to_args(args, code)

    mode_name = _resolve_mode_name(args)
    preset = resolve_mode(mode_name)

    # Merge preset → CLI args (CLI wins on explicit overrides).
    if args.biome is None:
        args.biome = preset.biome
    if args.fps is None:
        args.fps = preset.fps
    if not args.fullscreen and preset.fullscreen:
        args.fullscreen = True
    japanese = args.japanese or preset.japanese
    spring = args.spring or preset.spring
    ink_wash = args.ink_wash or preset.ink_wash

    # Mood: --mood pins; otherwise mode preset decides.
    if args.mood:
        mood = args.mood
        mood_pinned = True
    else:
        mood = preset.mood
        mood_pinned = preset.mood_pinned

    enable_events = preset.events_enabled and not args.no_events
    enable_rare = preset.rare_creatures_enabled and not args.no_rare
    enable_lore = preset.lore_enabled and not args.no_lore

    if ink_wash:
        apply_palette("inkwash")

    if args.no_logbook:
        logbook = None  # Aquarium will create an in-memory log
    else:
        logbook = Logbook.load(logbook_path())

    # Bump persistent launch counter (powers the "1-in-666" creature).
    launch_count = bump_launch_counter() if not args.no_logbook else 1

    options = AquariumOptions(
        japanese=japanese,
        spring=spring,
        ink_wash=ink_wash,
        biome=args.biome,
        fish_bob=not args.no_bob,
        caustics=not args.no_caustics,
        enable_bell=preset.enable_bell and not args.no_bell,
        enable_moods=enable_events or mood_pinned is False,
        enable_events=enable_events,
        enable_rare_creatures=enable_rare,
        enable_lore=enable_lore,
        initial_mood=mood if is_valid_mood(mood) else "calm",
        mood_pinned=mood_pinned,
        launch_count=launch_count,
        logbook=logbook,
    )

    rng = make_rng(seed=args.seed, prefer_quantum=args.quantum_seed)

    if args.print_code:
        # Print a deterministic tank code summarising the chosen options.
        modifier = ""
        if japanese and ink_wash:
            modifier = "SUMI"
        elif japanese:
            modifier = "KOI"
        elif spring:
            modifier = "SPRING"
        elif mode_name == NIGHTWATCH:
            modifier = "NIGHTWATCH"
        seed_value = args.seed if args.seed is not None else 0
        sc = SeedCode(biome=args.biome, seed=seed_value, mood=mood, modifier=modifier)
        print(sc.serialize())
        return 0

    # Defer pygame import so ``--help`` / ``--version`` work without it.
    from .renderer import run

    return run(
        grid_w=max(40, args.width),
        grid_h=max(15, args.height),
        fps=max(1, args.fps),
        seed=args.seed,
        fullscreen=args.fullscreen,
        options=options,
        rng=rng,
        crt_scanlines=preset.crt_scanlines,
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
