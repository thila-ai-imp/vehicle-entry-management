@echo off
setlocal
cd /d "%~dp0"

set STAMP=%DATE:~-4%-%DATE:~3,2%-%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set STAMP=%STAMP: =0%
set DEST=%~dp0backups\%STAMP%

echo.
echo CMDA Vehicle Entry - Database backup
echo Project: %CD%
echo Target:  %DEST%
echo.
echo For the safest copy, stop the server window (Ctrl+C) first, then run this file.
echo.
pause

mkdir "%DEST%" 2>nul
if exist "cmda_yard.db" copy /Y "cmda_yard.db" "%DEST%\" >nul
if exist "cmda_yard.db-wal" copy /Y "cmda_yard.db-wal" "%DEST%\" >nul
if exist "cmda_yard.db-shm" copy /Y "cmda_yard.db-shm" "%DEST%\" >nul

echo.
echo Files in backup folder:
dir /b "%DEST%"
echo.
echo Done. Keep a second copy on a USB drive.
pause
