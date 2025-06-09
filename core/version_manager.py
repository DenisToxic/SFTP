"""Version management and auto-update functionality"""
import json
import os
import sys
import subprocess
import tempfile
import shutil
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication

from utils.config import ConfigManager

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available. Update checking will be disabled.")

try:
    from packaging import version
    PACKAGING_AVAILABLE = True
except ImportError:
    PACKAGING_AVAILABLE = False
    print("Warning: packaging library not available. Version comparison will be simplified.")


@dataclass
class VersionInfo:
    """Version information structure"""
    version: str
    release_date: str
    download_url: str
    changelog: str
    is_critical: bool = False
    min_version: str = "0.0.0"


class UpdateDownloader(QThread):
    """Background thread for downloading updates"""
    
    progress_updated = Signal(int, int)  # downloaded, total
    download_completed = Signal(str)  # file_path
    download_failed = Signal(str)  # error_message
    
    def __init__(self, download_url: str, file_path: str):
        """Initialize update downloader
        
        Args:
            download_url: URL to download from
            file_path: Local file path to save to
        """
        super().__init__()
        self.download_url = download_url
        self.file_path = file_path
        self._cancelled = False
        
    def run(self):
        """Download update file"""
        if not REQUESTS_AVAILABLE:
            self.download_failed.emit("Requests library not available")
            return
            
        try:
            import requests
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancelled:
                        return
                        
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress_updated.emit(downloaded, total_size)
                        
            self.download_completed.emit(self.file_path)
            
        except Exception as e:
            self.download_failed.emit(str(e))
            
    def cancel(self):
        """Cancel download"""
        self._cancelled = True


class VersionManager(QObject):
    """Manages application versioning and updates"""
    
    update_available = Signal(VersionInfo)
    update_check_completed = Signal(bool)  # has_update
    update_installed = Signal()
    update_failed = Signal(str)  # error_message
    
    # Configuration - UPDATE THIS TO 1.1.0 for the new version
    CURRENT_VERSION = "1.2.0"
    UPDATE_CHECK_URL = "https://api.github.com/repos/DenisToxic/SFTP/releases/latest"
    GITHUB_RELEASES_URL = "https://github.com/DenisToxic/SFTP/releases"
    UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000  # 24 hours in milliseconds
    
    # Installation paths
    PROGRAM_FILES_PATH = r"C:\Program Files\SFTP"
    APPDATA_PATH = os.path.join(os.environ.get('APPDATA', ''), 'SFTP GUI Manager')
    
    def __init__(self):
        """Initialize version manager"""
        super().__init__()
        self.config_manager = ConfigManager()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_for_updates)
        self.downloader = None
        self.progress_dialog = None
        
        # Load settings
        self.auto_check_enabled = self.config_manager.get("auto_update_check", True)
        self.auto_install_enabled = self.config_manager.get("auto_install_updates", False)
        self.include_prereleases = self.config_manager.get("include_prereleases", False)
        
        # Disable auto-check if requests is not available
        if not REQUESTS_AVAILABLE:
            self.auto_check_enabled = False
            print("Auto-update checking disabled due to missing dependencies")
        
        # Start auto-check timer if enabled
        if self.auto_check_enabled:
            self.start_auto_check()
            
    def get_installation_path(self) -> str:
        """Get the installation path for the application
        
        Returns:
            Installation directory path
        """
        if hasattr(sys, 'frozen'):
            # Running as executable - get the directory containing the exe
            exe_dir = os.path.dirname(sys.executable)
            
            # Check if we're in Program Files
            if self.PROGRAM_FILES_PATH.lower() in exe_dir.lower():
                return self.PROGRAM_FILES_PATH
            else:
                # Fallback to current directory
                return exe_dir
        else:
            # Development mode
            return os.path.dirname(os.path.abspath(__file__))
            
    def get_executable_path(self) -> str:
        """Get the path to the main executable
        
        Returns:
            Path to main.exe
        """
        if hasattr(sys, 'frozen'):
            return sys.executable
        else:
            # Development mode - return script path
            return os.path.join(self.get_installation_path(), "main.py")
            
    def start_auto_check(self):
        """Start automatic update checking"""
        if not REQUESTS_AVAILABLE:
            return
            
        # Check immediately on startup (after 5 seconds)
        QTimer.singleShot(5000, self.check_for_updates)
        
        # Then check periodically
        self.update_timer.start(self.UPDATE_CHECK_INTERVAL)
        
    def stop_auto_check(self):
        """Stop automatic update checking"""
        self.update_timer.stop()
        
    def get_current_version(self) -> str:
        """Get current application version
        
        Returns:
            Current version string
        """
        return self.CURRENT_VERSION
        
    def get_version_info(self) -> Dict:
        """Get detailed version information
        
        Returns:
            Dictionary with version information
        """
        return {
            "version": self.CURRENT_VERSION,
            "build_date": self._get_build_date(),
            "python_version": sys.version,
            "platform": sys.platform,
            "executable": self.get_executable_path(),
            "installation_path": self.get_installation_path(),
            "requests_available": REQUESTS_AVAILABLE,
            "packaging_available": PACKAGING_AVAILABLE
        }
        
    def _get_build_date(self) -> str:
        """Get application build date
        
        Returns:
            Build date as ISO string
        """
        try:
            # Try to get from executable modification time
            build_time = os.path.getmtime(self.get_executable_path())
            return datetime.fromtimestamp(build_time).isoformat()
        except:
            return "Unknown"
            
    def check_for_updates(self, silent: bool = True) -> None:
        """Check for available updates
        
        Args:
            silent: If True, don't show messages for no updates
        """
        if not REQUESTS_AVAILABLE:
            if not silent:
                QMessageBox.warning(
                    None, "Update Check Unavailable",
                    "Update checking is not available in this build.\n"
                    "Please check for updates manually at:\n"
                    f"{self.GITHUB_RELEASES_URL}"
                )
            self.update_check_completed.emit(False)
            return
            
        try:
            import requests
            
            # Make request to GitHub API
            response = requests.get(self.UPDATE_CHECK_URL, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            
            # Parse release information
            latest_version = release_data['tag_name'].lstrip('v')
            release_date = release_data['published_at']
            changelog = release_data['body']
            is_prerelease = release_data['prerelease']
            
            # Skip prereleases if not enabled
            if is_prerelease and not self.include_prereleases:
                self.update_check_completed.emit(False)
                return
                
            # Find download URL for current platform
            download_url = self._find_download_url(release_data['assets'])
            
            if not download_url:
                if not silent:
                    QMessageBox.warning(
                        None, "Update Check",
                        "No compatible download found for your platform."
                    )
                self.update_check_completed.emit(False)
                return
                
            # Compare versions
            if self._is_newer_version(latest_version, self.CURRENT_VERSION):
                version_info = VersionInfo(
                    version=latest_version,
                    release_date=release_date,
                    download_url=download_url,
                    changelog=changelog,
                    is_critical=self._is_critical_update(changelog)
                )
                
                # Update last check time
                self.config_manager.set("last_update_check", datetime.now().isoformat())
                self.config_manager.save_config()
                
                self.update_available.emit(version_info)
                self.update_check_completed.emit(True)
                
                # Auto-install if enabled and not critical
                if self.auto_install_enabled and not version_info.is_critical:
                    self.download_and_install_update(version_info)
                    
            else:
                if not silent:
                    QMessageBox.information(
                        None, "Update Check",
                        f"You are running the latest version ({self.CURRENT_VERSION})"
                    )
                self.update_check_completed.emit(False)
                
        except Exception as e:
            error_msg = str(e)
            if not silent:
                QMessageBox.warning(
                    None, "Update Check Failed",
                    f"Failed to check for updates:\n{error_msg}\n\n"
                    f"You can check for updates manually at:\n"
                    f"{self.GITHUB_RELEASES_URL}"
                )
            self.update_check_completed.emit(False)
            
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare two version strings
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            True if version1 is newer than version2
        """
        if PACKAGING_AVAILABLE:
            try:
                from packaging import version
                return version.parse(version1) > version.parse(version2)
            except:
                pass
                
        # Fallback to simple string comparison
        try:
            # Split versions into parts and compare numerically
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
        except:
            # Last resort: string comparison
            return version1 > version2
            
    def _find_download_url(self, assets: list) -> Optional[str]:
        """Find appropriate download URL for current platform
        
        Args:
            assets: List of release assets
            
        Returns:
            Download URL or None if not found
        """
        # Look for Windows installer first
        for asset in assets:
            name = asset['name'].lower()
            if 'setup.exe' in name or 'installer.exe' in name or name.endswith('_setup.exe'):
                return asset['browser_download_url']
        
        # Fallback to any Windows executable
        for asset in assets:
            name = asset['name'].lower()
            if 'windows' in name and name.endswith('.exe'):
                return asset['browser_download_url']
                
        # Last resort - any .exe file
        for asset in assets:
            name = asset['name'].lower()
            if name.endswith('.exe'):
                return asset['browser_download_url']
                
        return None
        
    def _is_critical_update(self, changelog: str) -> bool:
        """Determine if update is critical based on changelog
        
        Args:
            changelog: Release changelog
            
        Returns:
            True if critical update
        """
        critical_keywords = [
            'critical', 'security', 'vulnerability', 'urgent',
            'hotfix', 'emergency', 'important security'
        ]
        
        changelog_lower = changelog.lower()
        return any(keyword in changelog_lower for keyword in critical_keywords)
        
    def download_and_install_update(self, version_info: VersionInfo):
        """Download and install update
        
        Args:
            version_info: Version information
        """
        if not REQUESTS_AVAILABLE:
            self.update_failed.emit("Update downloads are not available in this build")
            return
        
        try:
            self.debug_update_process(f"Starting update download for version {version_info.version}")
            
            # Create temporary file for download
            temp_dir = tempfile.mkdtemp(prefix="sftp_update_")
            filename = os.path.basename(version_info.download_url)
            temp_file = os.path.join(temp_dir, filename)
            
            self.debug_update_process(f"Download URL: {version_info.download_url}")
            self.debug_update_process(f"Temp file: {temp_file}")
            
            # Show progress dialog
            self.progress_dialog = QProgressDialog(
                f"Downloading update {version_info.version}...",
                "Cancel", 0, 100
            )
            self.progress_dialog.setWindowTitle("Updating SFTP GUI Manager")
            self.progress_dialog.setModal(True)
            self.progress_dialog.show()
            
            # Start download
            self.downloader = UpdateDownloader(version_info.download_url, temp_file)
            self.downloader.progress_updated.connect(self._on_download_progress)
            self.downloader.download_completed.connect(
                lambda path: self._on_download_completed(path, version_info)
            )
            self.downloader.download_failed.connect(self._on_download_failed)
            
            self.progress_dialog.canceled.connect(self.downloader.cancel)
            
            self.downloader.start()
            
        except Exception as e:
            self.debug_update_process(f"Download setup failed: {str(e)}")
            self.update_failed.emit(f"Failed to start download: {str(e)}")
            
    def _on_download_progress(self, downloaded: int, total: int):
        """Handle download progress update
        
        Args:
            downloaded: Bytes downloaded
            total: Total bytes
        """
        if self.progress_dialog and total > 0:
            progress = int((downloaded / total) * 100)
            self.progress_dialog.setValue(progress)
            self.progress_dialog.setLabelText(
                f"Downloading... {downloaded // 1024}KB / {total // 1024}KB"
            )
            
    def _on_download_completed(self, file_path: str, version_info: VersionInfo):
        """Handle download completion
        
        Args:
            file_path: Downloaded file path
            version_info: Version information
        """
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        try:
            self.debug_update_process(f"Download completed: {file_path}")
            self.debug_update_process(f"File size: {os.path.getsize(file_path)} bytes")
            self._install_update(file_path, version_info)
        except Exception as e:
            self.debug_update_process(f"Installation failed: {str(e)}")
            self.update_failed.emit(f"Failed to install update: {str(e)}")
            
    def _on_download_failed(self, error_message: str):
        """Handle download failure
        
        Args:
            error_message: Error message
        """
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        self.update_failed.emit(f"Download failed: {error_message}")
        
    def _install_update(self, file_path: str, version_info: VersionInfo):
        """Install downloaded update
        
        Args:
            file_path: Downloaded file path
            version_info: Version information
        """
        try:
            # Check if it's an installer
            if file_path.lower().endswith(('setup.exe', 'installer.exe')) or 'setup' in file_path.lower():
                self._install_with_installer(file_path, version_info)
            else:
                self._install_executable_replacement(file_path, version_info)
                
        except Exception as e:
            self.update_failed.emit(f"Installation failed: {str(e)}")
            
    def _install_with_installer(self, installer_path: str, version_info: VersionInfo):
        """Install update using installer
        
        Args:
            installer_path: Path to installer executable
            version_info: Version information
        """
        # Show confirmation dialog
        reply = QMessageBox.question(
            None,
            "Install Update",
            f"Ready to install SFTP GUI Manager v{version_info.version}\n\n"
            f"The installer will run and the application will close.\n"
            f"Continue with the update?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Run installer with silent flags
                subprocess.Popen([installer_path, '/SILENT', '/CLOSEAPPLICATIONS'])
                
                self.update_installed.emit()
                QApplication.quit()
                
            except Exception as e:
                raise ValueError(f"Failed to run installer: {str(e)}")
        else:
            # Clean up downloaded file
            try:
                os.remove(installer_path)
            except:
                pass
                
    def _install_executable_replacement(self, new_exe_path: str, version_info: VersionInfo):
        """Install update by replacing executable (fallback method)
        
        Args:
            new_exe_path: Path to new executable
            version_info: Version information
        """
        try:
            # Get current executable path
            current_exe = self.get_executable_path()
            
            if not hasattr(sys, 'frozen'):
                # Development mode
                QMessageBox.information(
                    None, "Development Mode",
                    f"Update downloaded to: {new_exe_path}\n\n"
                    f"In development mode, please manually replace the executable."
                )
                self.update_installed.emit()
                return
        
            # Check if we can write to the installation directory
            install_dir = self.get_installation_path()
            if not os.access(install_dir, os.W_OK):
                QMessageBox.warning(
                    None, "Permission Error",
                    f"Cannot write to installation directory: {install_dir}\n\n"
                    f"Please run the installer as administrator or use the installer version."
                )
                return
        
            # Create backup of current executable
            backup_path = current_exe + ".backup"
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                shutil.copy2(current_exe, backup_path)
            except Exception as e:
                print(f"Warning: Could not create backup: {e}")
        
            # Create robust update script
            update_script = self._create_robust_update_script(new_exe_path, current_exe, backup_path)
        
            # Show confirmation dialog
            reply = QMessageBox.question(
                None,
                "Install Update",
                f"Ready to install SFTP GUI Manager v{version_info.version}\n\n"
                f"The application will close and restart automatically.\n"
                f"Continue with the update?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
        
            if reply == QMessageBox.Yes:
                # Execute update script and exit
                if sys.platform == 'win32':
                    # Use cmd /c to run the batch file
                    subprocess.Popen(['cmd', '/c', update_script], shell=False)
                else:
                    subprocess.Popen(['bash', update_script])
            
                self.update_installed.emit()
                QApplication.quit()
            else:
                # Clean up downloaded file
                try:
                    os.remove(new_exe_path)
                    os.remove(update_script)
                except:
                    pass
                
        except Exception as e:
            self.update_failed.emit(f"Installation failed: {str(e)}")
            
    def _create_robust_update_script(self, new_exe_path: str, current_exe_path: str, backup_path: str) -> str:
        """Create robust update script that handles Windows file locking
        
        Args:
            new_exe_path: Path to new executable
            current_exe_path: Path to current executable
            backup_path: Path to backup executable
            
        Returns:
            Path to update script
        """
        script_dir = os.path.dirname(new_exe_path)
        
        if sys.platform == 'win32':
            # Robust Windows batch script
            script_path = os.path.join(script_dir, "robust_update.bat")
            exe_name = os.path.basename(current_exe_path)
            
            script_content = f'''@echo off
setlocal enabledelayedexpansion

echo Updating SFTP GUI Manager...
echo Aktualisiere SFTP GUI Manager...

REM Wait for main application to close gracefully
echo Waiting for application to close...
echo Warte auf Schließen der Anwendung...
timeout /t 5 /nobreak >nul

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
        else:
            # Unix shell script (fallback)
            script_path = os.path.join(script_dir, "robust_update.sh")
            script_content = f'''#!/bin/bash
echo "Updating SFTP GUI Manager..."

# Wait for main application to close
sleep 5

# Kill any remaining instances
pkill -f "{os.path.basename(current_exe_path)}" || true
sleep 2

# Try to move current executable first
temp_old_exe="{current_exe_path}.old"
if mv "{current_exe_path}" "$temp_old_exe"; then
    echo "Moved current executable successfully"
    
    # Copy new executable
    if cp "{new_exe_path}" "{current_exe_path}"; then
        echo "Update successful!"
        chmod +x "{current_exe_path}"
        
        # Clean up
        rm -f "$temp_old_exe"
        rm -f "{new_exe_path}"
        rm -f "{backup_path}"
        
        # Restart application
        "{current_exe_path}" &
        
        # Remove this script
        (sleep 3; rm -f "$0") &
        exit 0
    else
        echo "Copy failed! Restoring original..."
        mv "$temp_old_exe" "{current_exe_path}"
    fi
fi

echo "Update failed! Restoring backup..."
if [ -f "{backup_path}" ]; then
    cp "{backup_path}" "{current_exe_path}"
    chmod +x "{current_exe_path}"
    echo "Backup restored"
else
    echo "No backup found!"
fi

echo "Press Enter to exit"
read
exit 1
'''
    
        # Write script
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make script executable on Unix
        if sys.platform != 'win32':
            os.chmod(script_path, 0o755)
        
        return script_path
        
    def debug_update_process(self, message: str):
        """Log debug information about the update process
        
        Args:
            message: Debug message
        """
        try:
            debug_dir = os.path.join(self.APPDATA_PATH, "update_logs")
            os.makedirs(debug_dir, exist_ok=True)
            
            log_file = os.path.join(debug_dir, "update_log.txt")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Debug logging failed: {e}")
            
    def show_update_debug_info(self):
        """Show update debug information dialog"""
        try:
            debug_info = {
                "Current Version": self.get_current_version(),
                "Executable Path": self.get_executable_path(),
                "Installation Path": self.get_installation_path(),
                "User Data Path": self.APPDATA_PATH,
                "Is Frozen": str(hasattr(sys, 'frozen')),
                "Platform": sys.platform,
                "Directory Writable": str(os.access(self.get_installation_path(), os.W_OK)),
                "Update Settings": str(self.get_update_settings())
            }
            
            # Format as text
            info_text = "Update System Debug Information:\n\n"
            for key, value in debug_info.items():
                info_text += f"{key}: {value}\n"
            
            # Add log file content if exists
            log_file = os.path.join(self.APPDATA_PATH, "update_logs", "update_log.txt")
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                    info_text += "\n\nUpdate Log:\n" + log_content
                except Exception as e:
                    info_text += f"\n\nError reading log file: {e}"
                
            # Show dialog
            QMessageBox.information(None, "Update Debug Information", info_text)
        
        except Exception as e:
            QMessageBox.critical(None, "Debug Error", f"Failed to gather debug info: {e}")
            
    def restart_application(self):
        """Restart the application"""
        try:
            exe_path = self.get_executable_path()
            subprocess.Popen([exe_path])
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(
                None, "Restart Failed",
                f"Failed to restart application: {str(e)}\n\n"
                f"Please restart manually."
            )
            
    def set_auto_check_enabled(self, enabled: bool):
        """Enable/disable automatic update checking
        
        Args:
            enabled: Enable auto-check
        """
        if not REQUESTS_AVAILABLE and enabled:
            return  # Can't enable if requests is not available
            
        self.auto_check_enabled = enabled
        self.config_manager.set("auto_update_check", enabled)
        self.config_manager.save_config()
        
        if enabled:
            self.start_auto_check()
        else:
            self.stop_auto_check()
            
    def set_auto_install_enabled(self, enabled: bool):
        """Enable/disable automatic update installation
        
        Args:
            enabled: Enable auto-install
        """
        if not REQUESTS_AVAILABLE and enabled:
            return  # Can't enable if requests is not available
            
        self.auto_install_enabled = enabled
        self.config_manager.set("auto_install_updates", enabled)
        self.config_manager.save_config()
        
    def set_include_prereleases(self, enabled: bool):
        """Enable/disable prerelease updates
        
        Args:
            enabled: Include prereleases
        """
        self.include_prereleases = enabled
        self.config_manager.set("include_prereleases", enabled)
        self.config_manager.save_config()
        
    def get_update_settings(self) -> Dict:
        """Get current update settings
        
        Returns:
            Dictionary with update settings
        """
        return {
            "auto_check_enabled": self.auto_check_enabled and REQUESTS_AVAILABLE,
            "auto_install_enabled": self.auto_install_enabled and REQUESTS_AVAILABLE,
            "include_prereleases": self.include_prereleases,
            "last_check": self.config_manager.get("last_update_check"),
            "check_interval_hours": self.UPDATE_CHECK_INTERVAL // (60 * 60 * 1000),
            "requests_available": REQUESTS_AVAILABLE,
            "packaging_available": PACKAGING_AVAILABLE,
            "installation_path": self.get_installation_path(),
            "executable_path": self.get_executable_path()
        }
