@echo off
title Park Wave - Smart Parking System (Interactive Web UI)
cd /d "%~dp0"

set PYTHON_EXE="C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe"

if exist %PYTHON_EXE% (
    %PYTHON_EXE% main.py
    goto :end
)

py -3.12 main.py 2>nul
if %ERRORLEVEL% equ 0 goto :end

py main.py 2>nul
if %ERRORLEVEL% equ 0 goto :end

python main.py

:end
pause
