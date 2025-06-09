"""
Debug version of onefile build with console output
"""
import os
import sys
import subprocess


def build_debug_onefile():
    """Build debug version with console enabled"""
    print("🔧 Building debug single-file executable...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--console',  # Enable console for debug output
        '--name=SFTPGUIManager_Debug',
        '--add-data=version.json;.',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=paramiko',
        '--hidden-import=winpty',
        '--debug=all',  # Enable all debug output
        '--clean',
        '--noconfirm',
        'main.py'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ Debug build successful!")
        print("Run dist/SFTPGUIManager_Debug.exe to see console output")
    else:
        print("❌ Debug build failed!")


if __name__ == "__main__":
    build_debug_onefile()
