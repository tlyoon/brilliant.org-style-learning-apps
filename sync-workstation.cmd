@echo off
setlocal
cd /d "%~dp0"

rem Project identity, account, subject/source settings, branch, and machine-local
rem paths are resolved from config\configure_project.toml plus local settings.

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 was not found or is not active.
  pause
  exit /b 2
)
python -m scripts.sync_configured_workstation %*
set "SYNC_EXIT=%ERRORLEVEL%"
echo.
if not "%SYNC_EXIT%"=="0" echo Workstation synchronization failed with exit code %SYNC_EXIT%.
pause
exit /b %SYNC_EXIT%
