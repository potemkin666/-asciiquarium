#!/usr/bin/env bash
# Double-click launcher for Asciiquarium on Linux.
# Most file managers (Nautilus, Dolphin, Thunar, ...) will execute a
# marked-executable .sh on double-click (in some you may need to enable
# "Allow executing file as program" in the file properties once).
#
# On first run this creates a local .venv and installs the package.
# Subsequent runs reuse it and start instantly.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
PYEXE="$VENV_DIR/bin/python"

if [ ! -x "$PYEXE" ]; then
    echo "[Asciiquarium] First run: creating virtual environment in $VENV_DIR ..."
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv "$VENV_DIR"
    elif command -v python >/dev/null 2>&1; then
        python -m venv "$VENV_DIR"
    else
        echo "[Asciiquarium] Python 3.9+ is required but was not found on PATH."
        exit 1
    fi
    echo "[Asciiquarium] Installing dependencies ..."
    "$PYEXE" -m pip install --upgrade pip >/dev/null
    "$PYEXE" -m pip install -e .
fi

exec "$PYEXE" -m asciiquarium "$@"
