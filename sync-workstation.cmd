@echo off
setlocal
cd /d "%~dp0"
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 was not found or is not active.
  pause
  exit /b 2
)
python scripts\sync_workstation.py %*
set "SYNC_EXIT=%ERRORLEVEL%"
echo.
if not "%SYNC_EXIT%"=="0" echo Workstation synchronization failed with exit code %SYNC_EXIT%.
pause
exit /b %SYNC_EXIT%
