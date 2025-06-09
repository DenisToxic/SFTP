@echo off
echo SFTP GUI Manager - Single File Build
echo ====================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "main.py" (
    echo Error: main.py not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Run the onefile build script
echo.
echo Building single-file executable...
python build_scripts\build_onefile.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Single-file build completed successfully!
    echo.
    echo Output files:
    echo - dist\SFTPGUIManager.exe
    echo - dist\SFTP_GUI_Manager_v1.0.0\
    echo - dist\SFTP_GUI_Manager_v1.0.0.zip
    echo.
    echo The single .exe file is ready to distribute!
    echo No installation required - just run the .exe file.
    pause
) else (
    echo.
    echo ❌ Build failed!
    pause
    exit /b 1
)
