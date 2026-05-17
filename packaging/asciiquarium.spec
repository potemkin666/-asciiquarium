# PyInstaller spec for asciiquarium.
#
# Used by scripts/build.sh and scripts/build.ps1, plus the release workflow.
# Produces a single-file, windowed application that bundles the assets/ dir.

import os
import sys

block_cipher = None

# Resolve repo root regardless of where PyInstaller was invoked from.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(SPEC)), os.pardir)  # noqa: F821
)
SRC_ROOT = os.path.join(REPO_ROOT, "src")
ASSETS_DIR = os.path.join(SRC_ROOT, "asciiquarium", "assets")

if sys.platform == "win32":
    icon_path = os.path.join(ASSETS_DIR, "icon.ico")
elif sys.platform == "darwin":
    icon_path = os.path.join(ASSETS_DIR, "icon.icns")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(ASSETS_DIR, "icon.png")
else:
    icon_path = os.path.join(ASSETS_DIR, "icon.png")

a = Analysis(  # noqa: F821
    [os.path.join(REPO_ROOT, "packaging", "launch.py")],
    pathex=[SRC_ROOT],
    binaries=[],
    datas=[(ASSETS_DIR, "asciiquarium/assets")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Asciiquarium",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,  # GUI app — no terminal flash on double-click
    icon=icon_path if os.path.exists(icon_path) else None,
)

if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        exe,
        name="Asciiquarium.app",
        icon=icon_path if os.path.exists(icon_path) else None,
        bundle_identifier="com.potemkin666.asciiquarium",
        info_plist={
            "CFBundleName": "Asciiquarium",
            "CFBundleDisplayName": "Asciiquarium",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "10.13",
            "NSHumanReadableCopyright": "GPL-2.0-or-later",
        },
    )
