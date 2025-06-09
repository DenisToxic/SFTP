"""
Create a more robust update script that handles Windows file locking issues
"""
import os
import sys
from pathlib import Path


def create_robust_update_script(new_exe_path: str, current_exe_path: str, backup_path: str) -> str:
    """Create a robust Windows update script that handles file locking
    
    Args:
        new_exe_path: Path to new executable
        current_exe_path: Path to current executable  
        backup_path: Path to backup executable
        
    Returns:
        Path to update script
    """
    script_dir = os.path.dirname(new_exe_path)
    script_path = os.path.join(script_dir, "robust_update.bat")
    
    # Get just the executable name for taskkill
    exe_name = os.path.basename(current_exe_path)
    
    script_content = f'''@echo off
setlocal enabledelayedexpansion

echo Updating SFTP GUI Manager...
echo Aktualisiere SFTP GUI Manager...

REM Wait for main application to close gracefully
echo Waiting for application to close...
echo Warte auf Schließen der Anwendung...
timeout /t 3 /nobreak >nul

REM Force kill any remaining instances with multiple attempts
echo Terminating any remaining processes...
echo Beende verbleibende Prozesse...

for /L %%i in (1,1,5) do (
    taskkill /F /IM "{exe_name}" /T >nul 2>&1
    timeout /t 1 /nobreak >nul
)

REM Additional wait to ensure file handles are released
echo Ensuring file handles are released...
echo Stelle sicher, dass Datei-Handles freigegeben werden...
timeout /t 3 /nobreak >nul

REM Try to delete the current executable first (this releases any locks)
echo Preparing for file replacement...
echo Bereite Dateiaustausch vor...

REM Create a temporary copy of the current exe with a different name
set "temp_old_exe={current_exe_path}.old"
if exist "!temp_old_exe!" del "!temp_old_exe!" >nul 2>&1

REM Try to move (rename) the current executable instead of copying over it
echo Attempting to move current executable...
echo Versuche aktuelle Datei zu verschieben...
move "{current_exe_path}" "!temp_old_exe!" >nul 2>&1

if errorlevel 1 (
    echo Failed to move current executable, trying alternative method...
    echo Verschieben fehlgeschlagen, versuche alternative Methode...
    
    REM Alternative: Try to copy over with retries
    for /L %%i in (1,1,10) do (
        echo Attempt %%i of 10...
        echo Versuch %%i von 10...
        
        copy /Y "{new_exe_path}" "{current_exe_path}" >nul 2>&1
        if not errorlevel 1 (
            echo File replacement successful on attempt %%i
            echo Dateiaustausch erfolgreich bei Versuch %%i
            goto :success
        )
        
        echo Attempt %%i failed, waiting and retrying...
        echo Versuch %%i fehlgeschlagen, warte und versuche erneut...
        timeout /t 2 /nobreak >nul
    )
    
    echo All copy attempts failed! Restoring backup...
    echo Alle Kopieversuche fehlgeschlagen! Stelle Backup wieder her...
    goto :restore_backup
)

REM Now copy the new executable to the original location
echo Copying new executable...
echo Kopiere neue Datei...
copy /Y "{new_exe_path}" "{current_exe_path}" >nul 2>&1

if errorlevel 1 (
    echo Copy failed! Restoring original executable...
    echo Kopieren fehlgeschlagen! Stelle ursprüngliche Datei wieder her...
    move "!temp_old_exe!" "{current_exe_path}" >nul 2>&1
    goto :restore_backup
)

:success
echo Update successful!
echo Update erfolgreich!

REM Clean up temporary files
if exist "!temp_old_exe!" del "!temp_old_exe!" >nul 2>&1
if exist "{new_exe_path}" del "{new_exe_path}" >nul 2>&1
if exist "{backup_path}" del "{backup_path}" >nul 2>&1

REM Start the new version
echo Starting new version...
echo Starte neue Version...
start "" "{current_exe_path}"

REM Wait a moment then delete this script
timeout /t 2 /nobreak >nul
del "%~f0" >nul 2>&1
exit /b 0

:restore_backup
echo Update failed! Restoring backup...
echo Update fehlgeschlagen! Stelle Backup wieder her...

if exist "{backup_path}" (
    copy /Y "{backup_path}" "{current_exe_path}" >nul 2>&1
    if not errorlevel 1 (
        echo Backup restored successfully
        echo Backup erfolgreich wiederhergestellt
    ) else (
        echo Failed to restore backup!
        echo Backup-Wiederherstellung fehlgeschlagen!
    )
) else (
    echo No backup file found!
    echo Keine Backup-Datei gefunden!
)

echo Press any key to exit
echo Beliebige Taste zum Beenden drücken
pause >nul
exit /b 1
'''
    
    # Write the script
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return script_path


def test_file_operations():
    """Test file operations to identify potential issues"""
    print("🔧 Testing File Operations")
    print("=" * 40)
    
    # Test current executable access
    if hasattr(sys, 'frozen'):
        current_exe = sys.executable
        print(f"Current executable: {current_exe}")
        
        # Test if we can read the file
        try:
            with open(current_exe, 'rb') as f:
                f.read(1024)  # Read first 1KB
            print("✅ Can read current executable")
        except Exception as e:
            print(f"❌ Cannot read current executable: {e}")
        
        # Test if directory is writable
        exe_dir = os.path.dirname(current_exe)
        test_file = os.path.join(exe_dir, "test_write.tmp")
        
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("✅ Directory is writable")
        except Exception as e:
            print(f"❌ Directory is not writable: {e}")
            
        # Test if we can create a copy of the executable
        try:
            import shutil
            test_copy = current_exe + ".test"
            shutil.copy2(current_exe, test_copy)
            os.remove(test_copy)
            print("✅ Can create executable copy")
        except Exception as e:
            print(f"❌ Cannot create executable copy: {e}")
    else:
        print("Running in development mode, skipping executable tests")


if __name__ == "__main__":
    test_file_operations()
    
    # Example usage
    if len(sys.argv) >= 4:
        new_exe = sys.argv[1]
        current_exe = sys.argv[2] 
        backup_exe = sys.argv[3]
        
        script_path = create_robust_update_script(new_exe, current_exe, backup_exe)
        print(f"Created robust update script: {script_path}")
    else:
        print("Usage: python create_robust_update_script.py <new_exe> <current_exe> <backup_exe>")
