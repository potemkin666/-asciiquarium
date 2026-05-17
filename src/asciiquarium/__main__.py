"""Command-line entry point for ``python -m asciiquarium`` and console scripts."""

from __future__ import annotations

import argparse
import sys

from .aquarium import BIOMES, AquariumOptions
from .colors import apply_palette
from .qrng import make_rng
from .version import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asciiquarium",
        description="A self-contained ASCII aquarium animation (Pygame).",
    )
    parser.add_argument("--width", type=int, default=132, help="grid width in cells (default: 132)")
    parser.add_argument("--height", type=int, default=40, help="grid height in cells (default: 40)")
    parser.add_argument("--fps", type=int, default=20, help="frames per second (default: 20)")
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
        default="default",
        help="biome preset (gradient + density tweaks)",
    )
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
    parser.add_argument("--version", action="version", version=f"asciiquarium {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.ink_wash:
        apply_palette("inkwash")

    options = AquariumOptions(
        japanese=args.japanese,
        spring=args.spring,
        ink_wash=args.ink_wash,
        biome=args.biome,
        fish_bob=not args.no_bob,
        caustics=not args.no_caustics,
        enable_bell=not args.no_bell,
    )

    rng = make_rng(seed=args.seed, prefer_quantum=args.quantum_seed)

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
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
