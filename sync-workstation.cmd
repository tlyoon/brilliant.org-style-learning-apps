@echo off
setlocal
cd /d "%~dp0"

rem Fresh-workstation defaults. Shared generator settings come from
rem config\generator.shared.toml after the repository is synchronized.
if not defined BRILLIANT_SYNC_LOGIN_NAME set "BRILLIANT_SYNC_LOGIN_NAME=tlyoon@gmail.com"
if not defined BRILLIANT_SYNC_BRANCH set "BRILLIANT_SYNC_BRANCH=main"

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 was not found or is not active.
  pause
  exit /b 2
)
python scripts\sync_workstation.py --login-name "%BRILLIANT_SYNC_LOGIN_NAME%" --branch "%BRILLIANT_SYNC_BRANCH%" %*
set "SYNC_EXIT=%ERRORLEVEL%"
echo.
if not "%SYNC_EXIT%"=="0" echo Workstation synchronization failed with exit code %SYNC_EXIT%.
pause
exit /b %SYNC_EXIT%
