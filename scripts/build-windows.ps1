# Build the Windows release artifacts for Abyssarium.
#
# This is the canonical user-facing Windows build script:
#   1. Installs build dependencies into the current Python environment.
#   2. Runs PyInstaller via packaging/asciiquarium.spec.
#   3. Stages the produced executable as dist/Abyssarium/Abyssarium.exe so the
#      Inno Setup script in packaging/windows/abyssarium.iss can pick it up.
#   4. Fails loudly if the executable is missing.
#
# It does NOT compile the Inno Setup installer itself — the release workflow
# does that on a runner that has Inno Setup installed. Developers can run
# `iscc packaging\windows\abyssarium.iss` manually after this script if they
# have Inno Setup installed locally.
#
# Usage (from the repository root):
#   powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1

$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    Write-Host "==> Installing build dependencies"
    python -m pip install --upgrade pip
    python -m pip install -e ".[build]"

    if (Test-Path build) { Remove-Item -Recurse -Force build }
    if (Test-Path dist)  { Remove-Item -Recurse -Force dist }

    Write-Host "==> Running PyInstaller"
    python -m PyInstaller --clean --noconfirm packaging/asciiquarium.spec

    # PyInstaller's spec names the binary "Asciiquarium.exe". Re-stage it under
    # the user-facing "Abyssarium" branding so the Inno Setup script (and any
    # portable distribution) can pick it up by a stable name. The internal
    # Python package stays `asciiquarium`; only the shipped artefact is
    # renamed.
    $built = Join-Path "dist" "Asciiquarium.exe"
    if (-not (Test-Path $built)) {
        throw "PyInstaller did not produce the expected binary at: $built"
    }

    $stage = Join-Path "dist" "Abyssarium"
    if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
    New-Item -ItemType Directory -Path $stage | Out-Null

    Copy-Item -Path $built -Destination (Join-Path $stage "Abyssarium.exe") -Force
    foreach ($doc in @("README.md", "LICENSE", "CREDITS.md")) {
        if (Test-Path $doc) {
            Copy-Item -Path $doc -Destination $stage -Force
        }
    }
    $icon = Join-Path "src/asciiquarium/assets" "icon.ico"
    if (Test-Path $icon) {
        Copy-Item -Path $icon -Destination (Join-Path $stage "icon.ico") -Force
    }

    $finalExe = Join-Path $stage "Abyssarium.exe"
    if (-not (Test-Path $finalExe)) {
        throw "Abyssarium.exe missing after staging: $finalExe"
    }

    Write-Host ""
    Write-Host "==> Build complete"
    Write-Host "Executable: $finalExe"
    Get-ChildItem $stage
}
finally {
    Pop-Location
}
