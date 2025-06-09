@echo off
echo Building SFTP GUI Manager Installer
echo ====================================

REM Get version from argument or use default
set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

echo Version: %VERSION%

REM Check if PyInstaller dist folder exists
if not exist "..\dist\main.exe" (
    echo Error: main.exe not found in dist folder
    echo Please run PyInstaller first:
    echo   pyinstaller main.spec
    pause
    exit /b 1
)

REM Create installer
echo.
echo Creating installer...
python create_installer.py %VERSION%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Installer build completed successfully!
    echo.
    echo Output files:
    dir output\*.exe /b
    echo.
    pause
) else (
    echo.
    echo ❌ Installer build failed!
    pause
    exit /b 1
)
