@echo off
setlocal
cd /d "%~dp0"

rem Fresh-workstation defaults. Edit these values when reusing this script for another project,
rem or define the matching BRILLIANT_SYNC_* environment variables before running it.
if not defined BRILLIANT_SYNC_PROJECTS_FOLDER_URL set "BRILLIANT_SYNC_PROJECTS_FOLDER_URL=https://drive.google.com/drive/folders/1OLsE45GrA3veNeyVi7usO5-utS8gYC0X"
if not defined BRILLIANT_SYNC_LOGIN_NAME set "BRILLIANT_SYNC_LOGIN_NAME=tlyoon@gmail.com"
if not defined BRILLIANT_SYNC_BRANCH set "BRILLIANT_SYNC_BRANCH=main"

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 was not found or is not active.
  pause
  exit /b 2
)
python scripts\sync_workstation.py --projects-folder "%BRILLIANT_SYNC_PROJECTS_FOLDER_URL%" --login-name "%BRILLIANT_SYNC_LOGIN_NAME%" --branch "%BRILLIANT_SYNC_BRANCH%" %*
set "SYNC_EXIT=%ERRORLEVEL%"
echo.
if not "%SYNC_EXIT%"=="0" echo Workstation synchronization failed with exit code %SYNC_EXIT%.
pause
exit /b %SYNC_EXIT%
