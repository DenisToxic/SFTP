"""
Simplified installer creator for SFTP GUI Manager
"""
import os
import sys
import subprocess
from pathlib import Path


def create_installer(version="1.0.0"):
    """Create installer for SFTP GUI Manager
    
    Args:
        version: Application version
    """
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    dist_dir = project_dir / "dist"
    output_dir = script_dir / "output"
    
    # Check if executable exists
    exe_path = dist_dir / "SFTPGUIManager.exe"
    if not exe_path.exists():
        print(f"❌ Executable not found: {exe_path}")
        print("Please build the application first:")
        print("  python build_scripts/build.py")
        return False
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Create Inno Setup script
    iss_content = f'''[Setup]
AppId={{{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}}}
AppName=SFTP GUI Manager
AppVersion={version}
AppPublisher=SFTP Development Team
AppPublisherURL=https://github.com/DenisToxic/SFTP
DefaultDirName={{autopf}}\\SFTP
DefaultGroupName=SFTP GUI Manager
OutputDir={output_dir}
OutputBaseFilename=SFTPGUIManager_v{version}_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={{app}}\\SFTPGUIManager.exe

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\SFTP GUI Manager"; Filename: "{{app}}\\SFTPGUIManager.exe"
Name: "{{autodesktop}}\\SFTP GUI Manager"; Filename: "{{app}}\\SFTPGUIManager.exe"

[Registry]
Root: HKLM; Subkey: "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\SFTPGUIManager.exe"; ValueType: string; ValueName: ""; ValueData: "{{app}}\\SFTPGUIManager.exe"; Flags: uninsdeletekey

[Run]
Filename: "{{app}}\\SFTPGUIManager.exe"; Description: "Launch SFTP GUI Manager"; Flags: nowait postinstall skipifsilent

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  Exec('taskkill.exe', '/F /IM SFTPGUIManager.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(1000);
end;
'''
    
    # Write ISS file
    iss_file = script_dir / "setup.iss"
    with open(iss_file, 'w', encoding='utf-8') as f:
        f.write(iss_content)
    
    print(f"✅ Created installer script: {iss_file}")
    
    # Try to build installer
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    iscc_exe = None
    for path in inno_paths:
        if os.path.exists(path):
            iscc_exe = path
            break
    
    if not iscc_exe:
        print("⚠️  Inno Setup not found. Script created but not built.")
        print("Download Inno Setup from: https://jrsoftware.org/isinfo.php")
        return True
    
    print(f"🔨 Building installer with: {iscc_exe}")
    
    result = subprocess.run([iscc_exe, str(iss_file)], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Installer built successfully!")
        print(f"📦 Output: {output_dir}")
        return True
    else:
        print(f"❌ Installer build failed: {result.stderr}")
        return False


def main():
    """Main function"""
    version = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
    create_installer(version)


if __name__ == "__main__":
    main()
