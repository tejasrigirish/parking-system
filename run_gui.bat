@echo off
title Park Wave - Smart Parking System (Tkinter Desktop Window)
cd /d "%~dp0"

set PYTHON_EXE="C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe"

if exist %PYTHON_EXE% (
    %PYTHON_EXE% app_gui.py
    goto :end
)

py -3.12 app_gui.py 2>nul
if %ERRORLEVEL% equ 0 goto :end

py app_gui.py 2>nul
if %ERRORLEVEL% equ 0 goto :end

python app_gui.py

:end
pause
