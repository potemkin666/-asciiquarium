"""asciiquarium — a self-contained ASCII aquarium animation.

A Python + Pygame reimplementation of Kirk Baucom's classic terminal
`asciiquarium`. The :mod:`asciiquarium` package can be run directly
(``python -m asciiquarium``) or installed and launched via the
``asciiquarium`` entry point. When packaged with PyInstaller it becomes
a true double-clickable application.
"""

from .version import __version__

__all__ = ["__version__"]
