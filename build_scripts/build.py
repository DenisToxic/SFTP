"""
Unified build script for SFTP GUI Manager
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


class SFTPBuilder:
    """Builder for SFTP GUI Manager"""
    
    def __init__(self, version="1.0.0"):
        """Initialize builder
        
        Args:
            version: Application version
        """
        self.version = version
        self.project_dir = Path(__file__).parent.parent
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        
    def clean(self):
        """Clean previous builds"""
        print("🧹 Cleaning previous builds...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, "__pycache__"]
        
        for dir_path in dirs_to_clean:
            if isinstance(dir_path, str):
                dir_path = Path(dir_path)
            if dir_path.exists():
                print(f"  Removing {dir_path}")
                shutil.rmtree(dir_path)
        
        # Clean .pyc files
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))
                    
    def check_dependencies(self):
        """Check required dependencies"""
        print("📋 Checking dependencies...")
        
        required = ['PySide6', 'paramiko', 'winpty', 'pyinstaller']
        optional = ['requests', 'packaging']
        
        missing_required = []
        missing_optional = []
        
        for package in required:
            try:
                __import__(package)
                print(f"  ✅ {package}")
            except ImportError:
                missing_required.append(package)
                print(f"  ❌ {package}")
        
        for package in optional:
            try:
                __import__(package)
                print(f"  ✅ {package} (optional)")
            except ImportError:
                missing_optional.append(package)
                print(f"  ⚠️  {package} (optional)")
        
        if missing_required:
            print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
            print(f"Install with: pip install {' '.join(missing_required)}")
            return False
            
        if missing_optional:
            print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
            print("Some features may be disabled.")
            
        return True
        
    def build_onefile(self):
        """Build single-file executable"""
        print("🔨 Building single-file executable...")
        
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
            '--exclude-module=tkinter',
            '--exclude-module=matplotlib',
            '--exclude-module=numpy',
            '--clean',
            '--noconfirm',
            str(self.project_dir / 'main.py')
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=self.project_dir)
        
        if result.returncode == 0:
            exe_path = self.dist_dir / "SFTPGUIManager.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✅ Build successful! Size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ Executable not found after build")
                return False
        else:
            print("❌ Build failed!")
            return False
            
    def create_package(self):
        """Create distribution package"""
        print("📦 Creating distribution package...")
        
        exe_path = self.dist_dir / "SFTPGUIManager.exe"
        if not exe_path.exists():
            print("❌ Executable not found")
            return False
            
        # Create package directory
        package_dir = self.dist_dir / f"SFTP_GUI_Manager_v{self.version}"
        package_dir.mkdir(exist_ok=True)
        
        # Copy executable
        shutil.copy2(exe_path, package_dir / "SFTPGUIManager.exe")
        
        # Create README
        readme_content = f"""SFTP GUI Manager v{self.version}

A modern, feature-rich SFTP client with integrated terminal support.

QUICK START:
1. Double-click SFTPGUIManager.exe
2. Enter your SSH connection details
3. Start managing your remote files!

FEATURES:
• Modern file browser with drag & drop support
• Integrated SSH terminal
• Edit remote files with your preferred editor
• Automatic file synchronization
• Progress tracking for large transfers
• Command shortcuts and automation
• Built-in update system

SYSTEM REQUIREMENTS:
• Windows 10 or later (64-bit)
• No additional software required

For support and updates:
https://github.com/DenisToxic/SFTP
"""
        
        with open(package_dir / "README.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
            
        # Copy license if exists
        license_file = self.project_dir / "LICENSE"
        if license_file.exists():
            shutil.copy2(license_file, package_dir / "LICENSE.txt")
            
        # Create ZIP archive
        zip_path = self.dist_dir / f"SFTP_GUI_Manager_v{self.version}"
        shutil.make_archive(str(zip_path), 'zip', str(package_dir))
        
        print(f"✅ Package created: {package_dir}")
        print(f"✅ ZIP archive: {zip_path}.zip")
        
        return True
        
    def build(self):
        """Run complete build process"""
        print(f"🚀 Building SFTP GUI Manager v{self.version}")
        print("=" * 50)
        
        if not self.check_dependencies():
            return False
            
        self.clean()
        
        if not self.build_onefile():
            return False
            
        if not self.create_package():
            return False
            
        print("\n✅ Build completed successfully!")
        print(f"\nOutput files:")
        print(f"  • dist/SFTPGUIManager.exe")
        print(f"  • dist/SFTP_GUI_Manager_v{self.version}/")
        print(f"  • dist/SFTP_GUI_Manager_v{self.version}.zip")
        
        return True


def main():
    """Main function"""
    version = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
    
    builder = SFTPBuilder(version)
    success = builder.build()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
