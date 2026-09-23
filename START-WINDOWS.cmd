@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 start.py
) else (
    python start.py
)
if errorlevel 1 (
    echo.
    echo Python 3.11 oder neuer installieren. Bei der Installation "Add python.exe to PATH" aktivieren.
)
pause
