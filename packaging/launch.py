"""PyInstaller entry point.

Plain script (run as ``__main__``) — so it must use absolute imports rather
than the package-relative imports that ``asciiquarium/__main__.py`` uses.
"""

from __future__ import annotations

import sys

from asciiquarium.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
