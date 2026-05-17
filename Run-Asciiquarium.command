#!/usr/bin/env bash
# Double-click launcher for Asciiquarium on macOS.
# Finder runs .command files in Terminal on double-click. On first run we
# create a local .venv and install the package; subsequent runs are fast.

set -e

# Resolve the directory of this script (the repo root), even when launched
# from Finder where the working directory is the user's home.
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
        echo "Install it from https://www.python.org/ and try again."
        read -r -p "Press Return to close this window..." _
        exit 1
    fi
    echo "[Asciiquarium] Installing dependencies ..."
    "$PYEXE" -m pip install --upgrade pip >/dev/null
    "$PYEXE" -m pip install -e .
fi

exec "$PYEXE" -m asciiquarium "$@"
