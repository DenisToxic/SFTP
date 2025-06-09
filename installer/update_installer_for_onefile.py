"""
Update installer script to work with onefile executable
"""
import os
import sys
import subprocess
from pathlib import Path


def create_onefile_installer():
    """Create installer for onefile executable"""
    
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    output_dir = script_dir / "output"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Check if onefile executable exists
    exe_path = project_dir / "dist" / "SFTPGUIManager.exe"
    if not exe_path.exists():
        print(f"Error: Onefile executable not found: {exe_path}")
        print("Please run the onefile build first:")
        print("  python build_scripts/build_onefile.py")
        return False
    
    # ISS content for onefile
    iss_content = f'''[Setup]
AppId={{{{12345678-1234-1234-1234-123456789012}}}}
AppName=SFTP GUI Manager
AppVersion=1.0.0
AppPublisher=SFTP Development Team
AppPublisherURL=https://github.com/DenisToxic/SFTP
DefaultDirName={{autopf}}\\SFTP
DefaultGroupName=SFTP GUI Manager
OutputDir={output_dir}
OutputBaseFilename=SFTPGUIManager_v1.0.0_Setup
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
var
  ResultCode: Integer;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  
  // Kill any running instances
  Exec('taskkill.exe', '/F /IM SFTPGUIManager.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  
  // Wait a moment for processes to close
  Sleep(1000);
end;
'''
    
    # Write ISS file
    iss_file = script_dir / "onefile_setup.iss"
    with open(iss_file, 'w', encoding='utf-8') as f:
        f.write(iss_content)
    
    print(f"Created installer script: {iss_file}")
    
    # Try to build installer
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    iscc_exe = None
    for path in inno_paths:
        if os.path.exists(path):
            iscc_exe = path
            break
    
    if not iscc_exe:
        print("Inno Setup not found. Installer script created but not built.")
        print("Install Inno Setup from: https://jrsoftware.org/isinfo.php")
        print(f"Then run: {iscc_exe} {iss_file}")
        return True
    
    print(f"Building installer with: {iscc_exe}")
    
    # Build installer
    result = subprocess.run([iscc_exe, str(iss_file)], 
                          capture_output=True, 
                          text=True)
    
    if result.returncode == 0:
        print("✅ Installer built successfully!")
        print(f"📁 Output: {output_dir}")
        return True
    else:
        print(f"❌ Installer build failed: {result.stderr}")
        return False


if __name__ == "__main__":
    create_onefile_installer()
