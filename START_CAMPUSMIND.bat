@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python environment...
  py -m venv .venv || goto :error
)
echo Installing or checking requirements...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
".venv\Scripts\python.exe" scripts\ensure_security_secrets.py || goto :error
echo Starting CampusMind. Initial website sync runs automatically.
".venv\Scripts\python.exe" main.py
goto :eof
:error
echo.
echo CampusMind could not start. Review the error shown above.
pause
exit /b 1
