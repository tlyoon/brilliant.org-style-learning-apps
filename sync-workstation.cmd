@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" was not found. Install Python 3.12 first.
  pause
  exit /b 2
)
py -3.12 scripts\sync_workstation.py %*
set "SYNC_EXIT=%ERRORLEVEL%"
echo.
if not "%SYNC_EXIT%"=="0" echo Workstation synchronization failed with exit code %SYNC_EXIT%.
pause
exit /b %SYNC_EXIT%
