# Build a double-clickable Asciiquarium.exe on Windows.
#
# Run from the repository root:
#   powershell -ExecutionPolicy Bypass -File scripts\build.ps1
$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
    python -m pip install --upgrade pip
    python -m pip install -e ".[build]"

    if (Test-Path build) { Remove-Item -Recurse -Force build }
    if (Test-Path dist)  { Remove-Item -Recurse -Force dist }

    python -m PyInstaller --clean --noconfirm packaging/asciiquarium.spec

    Write-Host ""
    Write-Host "Build complete. Artifacts in: $(Resolve-Path dist)"
    Get-ChildItem dist
}
finally {
    Pop-Location
}
