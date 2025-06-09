"""
SFTP GUI Manager Installer Creator
Creates an Inno Setup installer script and builds the installer
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path


class InstallerCreator:
    """Creates installer for SFTP GUI Manager"""
    
    def __init__(self, app_version="1.0.0"):
        """Initialize installer creator
        
        Args:
            app_version: Application version
        """
        self.app_version = app_version
        self.app_name = "SFTP GUI Manager"
        self.app_id = "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"
        self.publisher = "SFTP Development Team"
        self.website = "https://github.com/DenisToxic/SFTP"
        
        # Paths
        self.script_dir = Path(__file__).parent
        self.project_dir = self.script_dir.parent
        self.dist_dir = self.project_dir / "dist"
        self.output_dir = self.project_dir / "installer" / "output"
        
    def create_iss_script(self) -> str:
        """Create Inno Setup script
        
        Returns:
            Path to created .iss file
        """
        iss_content = f'''[Setup]
AppId={self.app_id}
AppName={self.app_name}
AppVersion={self.app_version}
AppVerName={self.app_name} {self.app_version}
AppPublisher={self.publisher}
AppPublisherURL={self.website}
AppSupportURL={self.website}/issues
AppUpdatesURL={self.website}/releases
DefaultDirName={{autopf}}\\SFTP
DefaultGroupName={self.app_name}
AllowNoIcons=yes
LicenseFile={self.project_dir}\\LICENSE
InfoBeforeFile={self.script_dir}\\install_info.txt
OutputDir={self.output_dir}
OutputBaseFilename=SFTPGUIManager_v{self.app_version}_Setup
SetupIconFile={self.script_dir}\\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={{app}}\\main.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "{self.dist_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{{group}}\\{self.app_name}"; Filename: "{{app}}\\main.exe"
Name: "{{group}}\\{{cm:ProgramOnTheWeb,{self.app_name}}}"; Filename: "{self.website}"
Name: "{{group}}\\{{cm:UninstallProgram,{self.app_name}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{self.app_name}"; Filename: "{{app}}\\main.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{self.app_name}"; Filename: "{{app}}\\main.exe"; Tasks: quicklaunchicon

[Registry]
Root: HKLM; Subkey: "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\main.exe"; ValueType: string; ValueName: ""; ValueData: "{{app}}\\main.exe"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\main.exe"; ValueType: string; ValueName: "Path"; ValueData: "{{app}}"; Flags: uninsdeletekey

[Run]
Filename: "{{app}}\\main.exe"; Description: "{{cm:LaunchProgram,{self.app_name}}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}\\config.json"
Type: filesandordirs; Name: "{{app}}\\logs"
Type: filesandordirs; Name: "{{app}}\\temp"

[Code]
var
  ResultCode: Integer;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create application data directory
    CreateDir(ExpandConstant('{{userappdata}}\\SFTP GUI Manager'));
    
    // Set proper permissions for the installation directory
    // This ensures the application can update itself
    Exec('icacls.exe', ExpandConstant('"{{app}}" /grant Users:(OI)(CI)M'), '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  // Check if application is running
  if CurPageID = wpReady then
  begin
    if CheckForMutexes('SFTPGUIManagerMutex') then
    begin
      MsgBox('SFTP GUI Manager is currently running. Please close it before continuing with the installation.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  
  // Kill any running instances
  Exec('taskkill.exe', '/F /IM main.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  
  // Wait a moment for processes to close
  Sleep(1000);
end;
'''

        # Create installer directory if it doesn't exist
        self.script_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write ISS file
        iss_file = self.script_dir / "setup.iss"
        with open(iss_file, 'w', encoding='utf-8') as f:
            f.write(iss_content)
            
        return str(iss_file)
        
    def create_support_files(self):
        """Create supporting files for installer"""
        
        # Create install info file
        install_info = f'''Welcome to {self.app_name} Setup

This will install {self.app_name} version {self.app_version} on your computer.

{self.app_name} is a modern, feature-rich SFTP client with integrated terminal support.

Features:
• Modern, intuitive file browser with tree-view navigation
• Integrated SSH terminal access alongside file management
• Drag & drop file uploads and downloads
• Edit remote files with your preferred editor
• Automatic retry logic for network operations
• Progress tracking for large file transfers
• Secure password storage with encryption
• Built-in update system to stay current

System Requirements:
• Windows 10 or later (64-bit)
• 100 MB free disk space
• Internet connection for updates

The application will be installed to C:\\Program Files\\SFTP\\
'''
        
        install_info_file = self.script_dir / "install_info.txt"
        with open(install_info_file, 'w', encoding='utf-8') as f:
            f.write(install_info)
            
        # Create basic LICENSE file if it doesn't exist
        license_file = self.project_dir / "LICENSE"
        if not license_file.exists():
            license_content = f'''MIT License

Copyright (c) 2024 {self.publisher}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
            with open(license_file, 'w', encoding='utf-8') as f:
                f.write(license_content)
                
        # Create a simple icon file placeholder
        icon_file = self.script_dir / "icon.ico"
        if not icon_file.exists():
            # Create a minimal ICO file (1x1 pixel)
            ico_data = bytes([
                0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00,
                0x18, 0x00, 0x30, 0x00, 0x00, 0x00, 0x16, 0x00, 0x00, 0x00, 0x28, 0x00,
                0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x01, 0x00,
                0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00
            ])
            with open(icon_file, 'wb') as f:
                f.write(ico_data)
                
    def build_installer(self, iss_file: str) -> bool:
        """Build installer using Inno Setup
        
        Args:
            iss_file: Path to .iss script file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Common Inno Setup installation paths
            inno_paths = [
                r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"C:\Program Files\Inno Setup 6\ISCC.exe",
                r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
                r"C:\Program Files\Inno Setup 5\ISCC.exe",
            ]
            
            # Find Inno Setup compiler
            iscc_exe = None
            for path in inno_paths:
                if os.path.exists(path):
                    iscc_exe = path
                    break
                    
            if not iscc_exe:
                print("Error: Inno Setup not found. Please install Inno Setup.")
                print("Download from: https://jrsoftware.org/isinfo.php")
                return False
                
            print(f"Building installer using: {iscc_exe}")
            print(f"Script file: {iss_file}")
            
            # Build installer
            result = subprocess.run([iscc_exe, iss_file], 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print("Installer built successfully!")
                print(f"Output directory: {self.output_dir}")
                return True
            else:
                print(f"Build failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                print(f"Standard output: {result.stdout}")
                return False
                
        except Exception as e:
            print(f"Failed to build installer: {e}")
            return False
            
    def create_installer(self) -> bool:
        """Create complete installer
        
        Returns:
            True if successful, False otherwise
        """
        print(f"Creating installer for {self.app_name} v{self.app_version}")
        
        # Check if dist directory exists
        if not self.dist_dir.exists():
            print(f"Error: Distribution directory not found: {self.dist_dir}")
            print("Please run PyInstaller first to create the distribution.")
            return False
            
        # Check if main executable exists
        main_exe = self.dist_dir / "main.exe"
        if not main_exe.exists():
            print(f"Error: Main executable not found: {main_exe}")
            return False
            
        print("Creating support files...")
        self.create_support_files()
        
        print("Creating Inno Setup script...")
        iss_file = self.create_iss_script()
        
        print("Building installer...")
        success = self.build_installer(iss_file)
        
        if success:
            print("\n✅ Installer created successfully!")
            print(f"📁 Location: {self.output_dir}")
            print(f"📦 Filename: SFTPGUIManager_v{self.app_version}_Setup.exe")
        else:
            print("\n❌ Failed to create installer")
            
        return success


def main():
    """Main function"""
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = "1.0.0"
        
    creator = InstallerCreator(version)
    success = creator.create_installer()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
