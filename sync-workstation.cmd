@echo off
setlocal
cd /d "%~dp0"

rem Project identity, account, subject/source settings, branch, and machine-local
rem paths are resolved from config\configure_project.toml plus local settings.
rem Prefer the repository venv so sync can repair a stale environment even when
rem Python 3.12 is not the machine-wide default.
set "PYTHON_CMD="
if exist ".venv\Scripts\python.exe" set "PYTHON_CMD=.venv\Scripts\python.exe"
if not defined PYTHON_CMD (
  py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if not defined PYTHON_CMD (
  python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo Python 3.12 was not found and no repository .venv is available.
  exit /b 2
)
%PYTHON_CMD% -m scripts.sync_configured_workstation %*
set "SYNC_EXIT=%ERRORLEVEL%"
if not "%SYNC_EXIT%"=="0" echo Workstation synchronization failed with exit code %SYNC_EXIT%.
exit /b %SYNC_EXIT%
