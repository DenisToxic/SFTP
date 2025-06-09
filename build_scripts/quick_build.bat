@echo off
echo Quick Build - SFTP GUI Manager
echo ==============================

REM Check if we're in the right directory
if not exist "..\main.py" (
    echo Error: main.py not found
    echo Please run this script from the build_scripts directory
    pause
    exit /b 1
)

echo Running quick build...
python quick_build.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Quick build completed!
    echo Check the dist folder for SFTPGUIManager.exe
) else (
    echo.
    echo ❌ Quick build failed!
)

pause
