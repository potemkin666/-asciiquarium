@echo off
REM Double-click launcher for Asciiquarium on Windows.
REM Creates a local virtual environment (.venv) on first run, installs the
REM package into it, and then launches the aquarium. Subsequent double-clicks
REM reuse the existing venv and start almost instantly.

setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PYEXE=%VENV_DIR%\Scripts\python.exe"

if not exist "%PYEXE%" (
    echo [Asciiquarium] First run: creating virtual environment in %VENV_DIR% ...
    where py >nul 2>&1
    if %errorlevel%==0 (
        py -3 -m venv "%VENV_DIR%"
    ) else (
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo [Asciiquarium] Failed to create virtual environment. Is Python 3.9+ installed?
        pause
        exit /b 1
    )
    echo [Asciiquarium] Installing dependencies ...
    "%PYEXE%" -m pip install --upgrade pip >nul
    "%PYEXE%" -m pip install -e .
    if errorlevel 1 (
        echo [Asciiquarium] Failed to install dependencies.
        pause
        exit /b 1
    )
)

"%PYEXE%" -m asciiquarium %*
set "EXITCODE=%errorlevel%"
if not "%EXITCODE%"=="0" (
    echo.
    echo [Asciiquarium] Exited with code %EXITCODE%.
    pause
)
exit /b %EXITCODE%
