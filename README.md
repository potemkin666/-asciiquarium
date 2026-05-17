# asciiquarium

A self-contained, **double-clickable** ASCII aquarium. A Python + Pygame
reimplementation of Kirk Baucom's classic Perl
[`asciiquarium`](https://robobunny.com/projects/asciiquarium/) — packaged as
native binaries so end users don't need to install Python or a terminal.

| Platform | Download                          | What you get                    |
|----------|-----------------------------------|---------------------------------|
| Windows  | `Asciiquarium-windows.zip`        | `Asciiquarium.exe` — double-click |
| macOS    | `Asciiquarium-macos.zip`          | `Asciiquarium.app` — drag into `/Applications` |
| Linux    | `Asciiquarium-linux.tar.gz`       | `Asciiquarium` + `.desktop` file |

Grab the latest from the [Releases](../../releases) page.

## Install on Windows

1. Go to the [Releases](../../releases) page.
2. Download `Abyssarium-Setup-Windows.exe`.
3. Double-click it.
4. Launch Abyssarium from the Start Menu or Desktop shortcut.

No Python required. No terminal required. No unzipping required.

## Controls

| Key            | Action            |
|----------------|-------------------|
| `q` / `Esc`    | Quit              |
| `p`            | Pause / resume    |
| `r`            | Redraw / restart  |
| `f`            | Toggle fullscreen |

## Run from source

```bash
git clone https://github.com/potemkin666/-asciiquarium.git
cd -asciiquarium
python -m pip install -e .
python -m asciiquarium
```

Useful flags:

```bash
python -m asciiquarium --width 160 --height 50 --fullscreen --seed 42
```

## Build your own double-clickable binary

Requires Python 3.9+ and a working compiler toolchain on your OS.

```bash
# macOS / Linux
./scripts/build.sh

# Windows (single-file .exe)
powershell -ExecutionPolicy Bypass -File scripts\build.ps1

# Windows (staged for the Inno Setup installer at packaging/windows/abyssarium.iss)
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
```

Artifacts land in `dist/`. Under the hood this runs
[PyInstaller](https://pyinstaller.org/) with `packaging/asciiquarium.spec`.
On Windows, `scripts\build-windows.ps1` additionally stages the executable as
`dist\Abyssarium\Abyssarium.exe` so that
[Inno Setup](https://jrsoftware.org/isinfo.php) can compile
`packaging\windows\abyssarium.iss` into `Abyssarium-Setup-Windows.exe`.

On every tagged release (`v*`) GitHub Actions builds all three platforms
automatically and attaches them to a GitHub Release — see
[`.github/workflows/release.yml`](.github/workflows/release.yml).

## Developer run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m asciiquarium
```

On macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m asciiquarium
```

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m black --check .
```

The simulation (`asciiquarium.engine`, `asciiquarium.aquarium`) is fully
pygame-free, so all unit tests run headless. Only `asciiquarium.renderer`
touches pygame.

```
src/asciiquarium/
├── __init__.py          # package + version
├── __main__.py          # CLI entry point
├── aquarium.py          # high-level scene: backgrounds + spawning
├── colors.py            # ANSI-like color palette
├── engine.py            # Grid, Sprite, Scene
├── renderer.py          # Pygame window + main loop
├── sprites.py           # ASCII art
└── assets/              # icons bundled into the executable
```

## License & credits

GPL-2.0-or-later. See [`LICENSE`](LICENSE) and [`CREDITS.md`](CREDITS.md).
