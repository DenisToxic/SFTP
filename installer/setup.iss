[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName=SFTP GUI Manager
AppVersion=1.0.0
AppPublisher=SFTP Development Team
AppPublisherURL=https://github.com/DenisToxic/SFTP
DefaultDirName={autopf}\SFTP
DefaultGroupName=SFTP GUI Manager
OutputDir=S:\SFTP\github\installer\output
OutputBaseFilename=SFTPGUIManager_v1.0.0_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={app}\SFTPGUIManager.exe

[Files]
Source: "S:\SFTP\github\dist\SFTPGUIManager.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SFTP GUI Manager"; Filename: "{app}\SFTPGUIManager.exe"
Name: "{autodesktop}\SFTP GUI Manager"; Filename: "{app}\SFTPGUIManager.exe"

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\SFTPGUIManager.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\SFTPGUIManager.exe"; Flags: uninsdeletekey

[Run]
Filename: "{app}\SFTPGUIManager.exe"; Description: "Launch SFTP GUI Manager"; Flags: nowait postinstall skipifsilent

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  Exec('taskkill.exe', '/F /IM SFTPGUIManager.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(1000);
end;
