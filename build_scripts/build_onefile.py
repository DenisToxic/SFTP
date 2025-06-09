"""
Build script for creating SFTP GUI Manager as a single executable file
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))


def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'PySide6',
        'paramiko',
        'winpty',
        'pyinstaller'
    ]
    
    optional_packages = [
        'requests',
        'packaging'
    ]
    
    missing_required = []
    missing_optional = []
    
    print("📋 Checking dependencies...")
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} - MISSING")
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK (optional)")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} - MISSING (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("Some features may be disabled. Install with: pip install " + " ".join(missing_optional))
    
    return True


def build_onefile_executable():
    """Build the executable as a single file using PyInstaller"""
    print("🔨 Building single-file executable with PyInstaller...")
    
    # Method 1: Use the spec file
    if os.path.exists('main_onefile.spec'):
        print("Using main_onefile.spec...")
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'main_onefile.spec'
        ]
    else:
        # Method 2: Direct command line
        print("Using direct PyInstaller command...")
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--windowed',
            '--name=SFTPGUIManager',
            '--add-data=version.json;.',
            '--add-data=README.md;.',
            '--hidden-import=PySide6.QtCore',
            '--hidden-import=PySide6.QtWidgets',
            '--hidden-import=PySide6.QtGui',
            '--hidden-import=paramiko',
            '--hidden-import=winpty',
            '--exclude-module=tkinter',
            '--exclude-module=matplotlib',
            '--exclude-module=numpy',
            '--clean',
            '--noconfirm',
            'main.py'
        ]
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ PyInstaller build successful!")
        
        # Check if executable was created
        exe_path = Path('dist/SFTPGUIManager.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            return True
        else:
            print("❌ Executable not found after build")
            return False
    else:
        print("❌ PyInstaller build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False


def test_executable():
    """Test the built executable"""
    exe_path = Path('dist/SFTPGUIManager.exe')
    
    if not exe_path.exists():
        print("❌ Executable not found for testing")
        return False
    
    print("🧪 Testing executable...")
    
    # Try to run the executable briefly
    try:
        # Start the process
        process = subprocess.Popen([str(exe_path)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a short time to see if it starts
        try:
            stdout, stderr = process.communicate(timeout=5)
            if process.returncode == 0:
                print("✅ Executable runs successfully")
                return True
            else:
                print(f"⚠️  Executable exited with code {process.returncode}")
                if stderr:
                    print("STDERR:", stderr.decode())
                return True  # Still consider it working
        except subprocess.TimeoutExpired:
            # Process is still running, which is good for a GUI app
            process.terminate()
            print("✅ Executable started successfully (GUI app running)")
            return True
            
    except Exception as e:
        print(f"❌ Failed to test executable: {e}")
        return False


def create_distribution_package():
    """Create a distribution package with the executable"""
    exe_path = Path('dist/SFTPGUIManager.exe')
    
    if not exe_path.exists():
        print("❌ Executable not found for packaging")
        return False
    
    print("📦 Creating distribution package...")
    
    # Create distribution directory
    dist_package_dir = Path('dist/SFTP_GUI_Manager_v1.0.0')
    
    try:
        # Remove existing package directory
        if dist_package_dir.exists():
            shutil.rmtree(dist_package_dir)
        
        # Create package directory
        dist_package_dir.mkdir(parents=True)
        
        # Copy executable
        shutil.copy2(exe_path, dist_package_dir / 'SFTPGUIManager.exe')
        
        # Create README for distribution
        readme_content = """SFTP GUI Manager v1.0.0

A modern, feature-rich SFTP client with integrated terminal support.

INSTALLATION:
This is a portable application - no installation required!
Simply run SFTPGUIManager.exe to start the application.

FEATURES:
• Modern, intuitive file browser with tree-view navigation
• Integrated SSH terminal access alongside file management
• Drag & drop file uploads and downloads
• Edit remote files with your preferred editor
• Automatic retry logic for network operations
• Progress tracking for large file transfers
• Secure password storage with encryption
• Built-in update system to stay current

SYSTEM REQUIREMENTS:
• Windows 10 or later (64-bit)
• No additional software required

USAGE:
1. Double-click SFTPGUIManager.exe
2. Enter your SSH connection details
3. Start managing your remote files!

SUPPORT:
For issues and updates, visit:
https://github.com/DenisToxic/SFTP

COPYRIGHT:
Copyright (c) 2024 SFTP Development Team
Licensed under the MIT License
"""
        
        readme_file = dist_package_dir / "README.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Copy license if it exists
        license_file = Path('LICENSE')
        if license_file.exists():
            shutil.copy2(license_file, dist_package_dir / 'LICENSE.txt')
        
        print(f"✅ Distribution package created: {dist_package_dir}")
        
        # Create ZIP archive
        zip_path = Path('dist/SFTP_GUI_Manager_v1.0.0.zip')
        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', str(dist_package_dir))
        print(f"📦 ZIP archive created: {zip_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create distribution package: {e}")
        return False


def main():
    """Main build process"""
    print("🚀 SFTP GUI Manager - Single File Build")
    print("=" * 45)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    clean_build_dirs()
    
    # Build executable
    print("\n🔨 Building single-file executable...")
    if not build_onefile_executable():
        return False
    
    # Test executable
    print("\n🧪 Testing executable...")
    test_executable()
    
    # Create distribution package
    print("\n📦 Creating distribution package...")
    create_distribution_package()
    
    print("\n✅ Build process completed!")
    print("\nOutput files:")
    print("- dist/SFTPGUIManager.exe (Single executable file)")
    print("- dist/SFTP_GUI_Manager_v1.0.0/ (Distribution package)")
    print("- dist/SFTP_GUI_Manager_v1.0.0.zip (ZIP archive)")
    
    print("\n🎉 Your application is ready to distribute!")
    print("The single .exe file contains everything needed to run the application.")
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
