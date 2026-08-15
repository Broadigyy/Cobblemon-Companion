@echo off
cd /d "%~dp0"
python cobblemon_companion.py
if errorlevel 1 (
  echo.
  echo Cobblemon Companion failed to launch.
  echo Make sure Python is installed and available as "python".
  pause
)
