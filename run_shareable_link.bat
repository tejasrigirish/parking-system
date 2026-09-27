@echo off
title Park Wave - Smart Parking Public Shareable Link
cd /d "%~dp0"

set PYTHON_EXE="C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe"

if exist %PYTHON_EXE% (
    %PYTHON_EXE% share_tunnel.py
    goto :end
)

py -3 share_tunnel.py 2>nul
if %ERRORLEVEL% equ 0 goto :end

py share_tunnel.py 2>nul
if %ERRORLEVEL% equ 0 goto :end

python share_tunnel.py

:end
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred while starting the application.
    pause
)
