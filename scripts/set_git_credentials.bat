@echo off
echo SFTP GUI Manager - Set Git Credentials
echo =====================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Run the script
python set_git_credentials.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Git credentials set successfully!
) else (
    echo.
    echo ❌ Failed to set Git credentials!
    pause
    exit /b 1
)

pause
