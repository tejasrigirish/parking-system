@echo off
cd /d "%~dp0"

set PYTHON_EXE="C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe"

if exist %PYTHON_EXE% (
    start "Park Wave Smart Parking CLI" cmd /k "%PYTHON_EXE% main_cli.py"
    exit /b 0
)

start "Park Wave Smart Parking CLI" cmd /k "python main_cli.py"
exit /b 0
