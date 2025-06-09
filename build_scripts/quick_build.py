"""
Quick build script that bypasses dependency checks
"""
import sys
import subprocess
from pathlib import Path


def quick_build():
    """Quick build without extensive checks"""
    print("🚀 Quick Build - SFTP GUI Manager")
    print("=" * 40)
    
    project_dir = Path(__file__).parent.parent
    
    # Check if main.py exists
    main_py = project_dir / "main.py"
    if not main_py.exists():
        print(f"❌ main.py not found at {main_py}")
        return False
    
    print(f"📁 Project directory: {project_dir}")
    print(f"🐍 Python executable: {sys.executable}")
    
    # Build command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=SFTPGUIManager',
        '--add-data=version.json;.',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=paramiko',
        '--hidden-import=winpty',
        '--clean',
        '--noconfirm',
        str(main_py)
    ]
    
    print("🔨 Building executable...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=project_dir)
        
        if result.returncode == 0:
            # Check if executable was created
            exe_path = project_dir / "dist" / "SFTPGUIManager.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✅ Build successful!")
                print(f"📦 Executable: {exe_path}")
                print(f"📏 Size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ Build completed but executable not found")
                return False
        else:
            print(f"❌ Build failed with exit code {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False


if __name__ == "__main__":
    success = quick_build()
    if not success:
        sys.exit(1)
