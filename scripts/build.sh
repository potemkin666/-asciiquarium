#!/usr/bin/env bash
# Build a double-clickable Asciiquarium binary for the current platform.
#
# Output goes to dist/. macOS produces Asciiquarium.app; Linux produces
# an Asciiquarium binary; Windows builds via build.ps1 instead.
set -euo pipefail

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
python -m pip install -e ".[build]"

rm -rf build dist
python -m PyInstaller --clean --noconfirm packaging/asciiquarium.spec

echo
echo "Build complete. Artifacts in: $(pwd)/dist"
ls -la dist/
