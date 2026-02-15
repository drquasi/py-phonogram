@echo off
title The Phonograph Launch Script
echo ========================================
echo Starting The Phonograph Discord Bot...
echo ========================================
echo.

:: Check if the virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Could not find the virtual environment at .venv\Scripts\python.exe
    echo Please make sure your virtual environment folder is named ".venv"
    echo and is located in this directory.
    echo.
    pause
    exit /b
)

:: Run the bot
echo [INFO] Running Phonograph module...
".venv\Scripts\python.exe" -m src.phonograph

:: If we reach here, the bot has stopped
echo.
echo ========================================
echo Bot has stopped running.
echo ========================================
pause
