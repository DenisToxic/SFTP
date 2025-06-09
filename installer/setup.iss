[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=SFTP GUI Manager
AppVersion=1.0.0
AppVerName=SFTP GUI Manager 1.0.0
AppPublisher=SFTP Development Team
AppPublisherURL=https://github.com/DenisToxic/SFTP
AppSupportURL=https://github.com/DenisToxic/SFTP/issues
AppUpdatesURL=https://github.com/DenisToxic/SFTP/releases
DefaultDirName={autopf}\SFTP
DefaultGroupName=SFTP GUI Manager
AllowNoIcons=yes
LicenseFile=S:\SFTP\github\LICENSE
InfoBeforeFile=S:\SFTP\github\installer\install_info.txt
OutputDir=S:\SFTP\github\installer\output
OutputBaseFilename=SFTPGUIManager_v1.0.0_Setup
SetupIconFile=S:\SFTP\github\installer\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\main.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "S:\SFTP\github\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\SFTP GUI Manager"; Filename: "{app}\main.exe"
Name: "{group}\{cm:ProgramOnTheWeb,SFTP GUI Manager}"; Filename: "https://github.com/DenisToxic/SFTP"
Name: "{group}\{cm:UninstallProgram,SFTP GUI Manager}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SFTP GUI Manager"; Filename: "{app}\main.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\SFTP GUI Manager"; Filename: "{app}\main.exe"; Tasks: quicklaunchicon

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\main.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\main.exe"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\main.exe"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,SFTP GUI Manager}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\config.json"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\temp"

[Code]
var
  ResultCode: Integer;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create application data directory
    CreateDir(ExpandConstant('{userappdata}\SFTP GUI Manager'));
    
    // Set proper permissions for the installation directory
    // This ensures the application can update itself
    Exec('icacls.exe', ExpandConstant('"{app}" /grant Users:(OI)(CI)M'), '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
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
