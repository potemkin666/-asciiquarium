"""Command-line entry point for ``python -m asciiquarium`` and console scripts."""

from __future__ import annotations

import argparse
import sys

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
    parser.add_argument("--fullscreen", action="store_true", help="launch in fullscreen mode")
    parser.add_argument("--version", action="version", version=f"asciiquarium {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    # Defer pygame import so ``--help`` / ``--version`` work without it.
    from .renderer import run

    return run(
        grid_w=max(40, args.width),
        grid_h=max(15, args.height),
        fps=max(1, args.fps),
        seed=args.seed,
        fullscreen=args.fullscreen,
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
