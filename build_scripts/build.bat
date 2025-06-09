@echo off
echo SFTP GUI Manager - Build Script
echo ===============================

REM Get version from argument or use default
set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

echo Building version: %VERSION%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "..\main.py" (
    echo Error: main.py not found
    echo Please run this script from the build_scripts directory
    pause
    exit /b 1
)

REM Run the build script
python build.py %VERSION%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build completed successfully!
    echo.
    echo You can now run the installer build if needed.
) else (
    echo.
    echo ❌ Build failed!
)

pause
