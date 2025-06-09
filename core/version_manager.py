"""Version management and auto-update functionality"""
import json
import os
import sys
import subprocess
import tempfile
import zipfile
import shutil
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import requests
from packaging import version
from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication

from utils.config import ConfigManager


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
        try:
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
    
    # Configuration
    CURRENT_VERSION = "1.0.0"
    UPDATE_CHECK_URL = "https://api.github.com/repos/DenisToxic/SFTP/releases/latest"
    GITHUB_RELEASES_URL = "https://github.com/DenisToxic/SFTP/releases"
    UPDATE_CHECK_INTERVAL = 24 * 60 * 60 * 1000  # 24 hours in milliseconds
    
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
        
        # Start auto-check timer if enabled
        if self.auto_check_enabled:
            self.start_auto_check()
            
    def start_auto_check(self):
        """Start automatic update checking"""
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
            "executable": sys.executable
        }
        
    def _get_build_date(self) -> str:
        """Get application build date
        
        Returns:
            Build date as ISO string
        """
        try:
            # Try to get from executable modification time
            if hasattr(sys, 'frozen'):
                build_time = os.path.getmtime(sys.executable)
            else:
                build_time = os.path.getmtime(__file__)
            return datetime.fromtimestamp(build_time).isoformat()
        except:
            return "Unknown"
            
    def check_for_updates(self, silent: bool = True) -> None:
        """Check for available updates
        
        Args:
            silent: If True, don't show messages for no updates
        """
        try:
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
            if version.parse(latest_version) > version.parse(self.CURRENT_VERSION):
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
                
        except requests.RequestException as e:
            if not silent:
                QMessageBox.warning(
                    None, "Update Check Failed",
                    f"Failed to check for updates:\n{str(e)}"
                )
            self.update_check_completed.emit(False)
            
        except Exception as e:
            if not silent:
                QMessageBox.critical(
                    None, "Update Check Error",
                    f"An error occurred while checking for updates:\n{str(e)}"
                )
            self.update_check_completed.emit(False)
            
    def _find_download_url(self, assets: list) -> Optional[str]:
        """Find appropriate download URL for current platform
        
        Args:
            assets: List of release assets
            
        Returns:
            Download URL or None if not found
        """
        platform_map = {
            'win32': ['windows', 'win'],
            'darwin': ['macos', 'mac', 'darwin'],
            'linux': ['linux']
        }
        
        current_platform = sys.platform
        platform_keywords = platform_map.get(current_platform, [])
        
        # Look for platform-specific downloads
        for asset in assets:
            name = asset['name'].lower()
            if any(keyword in name for keyword in platform_keywords):
                return asset['browser_download_url']
                
        # Fallback to generic download
        for asset in assets:
            name = asset['name'].lower()
            if name.endswith(('.zip', '.tar.gz', '.exe', '.dmg', '.deb', '.rpm')):
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
        try:
            # Create temporary file for download
            temp_dir = tempfile.mkdtemp(prefix="sftp_update_")
            filename = os.path.basename(version_info.download_url)
            temp_file = os.path.join(temp_dir, filename)
            
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
            self._install_update(file_path, version_info)
        except Exception as e:
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
            if file_path.endswith('.zip'):
                self._install_zip_update(file_path, version_info)
            elif file_path.endswith('.exe'):
                self._install_exe_update(file_path, version_info)
            else:
                raise ValueError(f"Unsupported update format: {file_path}")
                
        except Exception as e:
            self.update_failed.emit(f"Installation failed: {str(e)}")
            
    def _install_zip_update(self, zip_path: str, version_info: VersionInfo):
        """Install update from ZIP file
        
        Args:
            zip_path: ZIP file path
            version_info: Version information
        """
        # Create backup of current installation
        backup_dir = self._create_backup()
        
        try:
            # Extract update
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_dir = tempfile.mkdtemp(prefix="sftp_extract_")
                zip_ref.extractall(extract_dir)
                
            # Find the main application directory in extracted files
            app_dir = self._find_app_directory(extract_dir)
            if not app_dir:
                raise ValueError("Could not find application directory in update")
                
            # Get current application directory
            if hasattr(sys, 'frozen'):
                current_dir = os.path.dirname(sys.executable)
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
            # Copy new files
            self._copy_update_files(app_dir, current_dir)
            
            # Update version info
            self._update_version_file(version_info)
            
            # Clean up
            shutil.rmtree(os.path.dirname(zip_path))
            shutil.rmtree(extract_dir)
            
            self.update_installed.emit()
            
            # Show restart dialog
            self._show_restart_dialog(version_info)
            
        except Exception as e:
            # Restore backup on failure
            if backup_dir and os.path.exists(backup_dir):
                self._restore_backup(backup_dir)
            raise e
            
    def _install_exe_update(self, exe_path: str, version_info: VersionInfo):
        """Install update from EXE file
        
        Args:
            exe_path: EXE file path
            version_info: Version information
        """
        try:
            # Run installer
            subprocess.run([exe_path, '/S'], check=True)  # Silent install
            
            # Clean up
            os.remove(exe_path)
            
            self.update_installed.emit()
            self._show_restart_dialog(version_info)
            
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Installer failed with code {e.returncode}")
            
    def _create_backup(self) -> str:
        """Create backup of current installation
        
        Returns:
            Backup directory path
        """
        try:
            if hasattr(sys, 'frozen'):
                current_dir = os.path.dirname(sys.executable)
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
            backup_dir = tempfile.mkdtemp(prefix="sftp_backup_")
            shutil.copytree(current_dir, os.path.join(backup_dir, "app"))
            
            return backup_dir
        except Exception:
            return None
            
    def _find_app_directory(self, extract_dir: str) -> Optional[str]:
        """Find application directory in extracted files
        
        Args:
            extract_dir: Extraction directory
            
        Returns:
            Application directory path or None
        """
        # Look for main.py or executable
        for root, dirs, files in os.walk(extract_dir):
            if 'main.py' in files or any(f.endswith('.exe') for f in files):
                return root
        return None
        
    def _copy_update_files(self, source_dir: str, target_dir: str):
        """Copy update files to application directory
        
        Args:
            source_dir: Source directory
            target_dir: Target directory
        """
        for root, dirs, files in os.walk(source_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache']]
            
            for file in files:
                # Skip certain files
                if file.endswith(('.pyc', '.pyo')) or file.startswith('.'):
                    continue
                    
                source_file = os.path.join(root, file)
                rel_path = os.path.relpath(source_file, source_dir)
                target_file = os.path.join(target_dir, rel_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                
                # Copy file
                shutil.copy2(source_file, target_file)
                
    def _update_version_file(self, version_info: VersionInfo):
        """Update version information file
        
        Args:
            version_info: Version information
        """
        version_data = {
            "version": version_info.version,
            "release_date": version_info.release_date,
            "updated_at": datetime.now().isoformat()
        }
        
        version_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "version.json"
        )
        
        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
            
    def _restore_backup(self, backup_dir: str):
        """Restore from backup
        
        Args:
            backup_dir: Backup directory
        """
        try:
            if hasattr(sys, 'frozen'):
                current_dir = os.path.dirname(sys.executable)
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
            app_backup = os.path.join(backup_dir, "app")
            if os.path.exists(app_backup):
                shutil.rmtree(current_dir)
                shutil.copytree(app_backup, current_dir)
        except Exception as e:
            print(f"Failed to restore backup: {e}")
            
    def _show_restart_dialog(self, version_info: VersionInfo):
        """Show restart dialog after update
        
        Args:
            version_info: Version information
        """
        reply = QMessageBox.question(
            None,
            "Update Installed",
            f"SFTP GUI Manager has been updated to version {version_info.version}.\n\n"
            f"The application needs to restart to complete the update.\n\n"
            f"Restart now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.restart_application()
            
    def restart_application(self):
        """Restart the application"""
        try:
            if hasattr(sys, 'frozen'):
                # Running as executable
                subprocess.Popen([sys.executable])
            else:
                # Running as script
                subprocess.Popen([sys.executable] + sys.argv)
                
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
            "auto_check_enabled": self.auto_check_enabled,
            "auto_install_enabled": self.auto_install_enabled,
            "include_prereleases": self.include_prereleases,
            "last_check": self.config_manager.get("last_update_check"),
            "check_interval_hours": self.UPDATE_CHECK_INTERVAL // (60 * 60 * 1000)
        }
