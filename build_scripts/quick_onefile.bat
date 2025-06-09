@echo off
echo Quick Single-File Build
echo =======================

REM Simple one-command build
echo Building with PyInstaller --onefile...

pyinstaller --onefile --windowed --name=SFTPGUIManager --add-data=version.json;. --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtWidgets --hidden-import=PySide6.QtGui --hidden-import=paramiko --hidden-import=winpty --clean --noconfirm main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Quick build successful!
    echo Output: dist\SFTPGUIManager.exe
    echo.
    echo Testing executable...
    start dist\SFTPGUIManager.exe
) else (
    echo.
    echo ❌ Quick build failed!
)

pause
