@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please run START_CAMPUSMIND.bat once first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\sync_website_once.py
pause
