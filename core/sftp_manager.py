"""SFTP operations manager"""
import os
import stat
import posixpath
import time
import tempfile
import subprocess
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QGroupBox, QComboBox, QLabel, QMessageBox, QMenu, QInputDialog,
    QFileDialog, QProgressDialog, QApplication, QTreeWidgetItem
)
from PySide6.QtCore import Qt

from ui.widgets.remote_file_browser import RemoteFileBrowser
from utils.file_watcher import FileWatcher


class SftpManager(QWidget):
    """Main SFTP operations manager"""
    
    def __init__(self, ssh_client, sftp_client, host: str, port: int, username: str, password: str):
        """Initialize SFTP manager
        
        Args:
            ssh_client: SSH client instance
            sftp_client: SFTP client instance
            host: SSH server hostname
            port: SSH server port
            username: SSH username
            password: SSH password
        """
        super().__init__()
        self.ssh = ssh_client
        self.sftp = sftp_client
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.path_stack = []
        self.current_path = "."
        
        self._setup_ui()
        self.load_remote_directory(".")
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Navigation bar
        nav_layout = QHBoxLayout()
        
        back_btn = QPushButton("⬅ Back")
        back_btn.clicked.connect(self.go_back)
        back_btn.setToolTip("Go back to previous directory")
        
        up_btn = QPushButton("⬆ Up")
        up_btn.clicked.connect(self.go_up)
        up_btn.setToolTip("Go to parent directory")
        
        self.path_input = QLineEdit()
        self.path_input.returnPressed.connect(self.go_to_path)
        self.path_input.setToolTip("Current directory path")
        
        nav_layout.addWidget(back_btn)
        nav_layout.addWidget(up_btn)
        nav_layout.addWidget(self.path_input)
        
        layout.addLayout(nav_layout)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        settings_layout.addWidget(QLabel("Default Editor:"))
        self.editor_combo = QComboBox()
        self.editor_combo.addItems(["notepad.exe", "code", "notepad++", "gedit", "vim"])
        settings_layout.addWidget(self.editor_combo)
        
        layout.addWidget(settings_group)
        
        # File browser
        self.file_browser = RemoteFileBrowser(self)
        self.file_browser.itemDoubleClicked.connect(self._handle_double_click)
        self.file_browser.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.file_browser)
        
    def _handle_double_click(self, item, column):
        """Handle double-click on file browser items"""
        file_info = item.data(0, Qt.UserRole)
        
        if stat.S_ISDIR(file_info.st_mode):
            # Navigate to directory
            new_path = posixpath.join(self.current_path, file_info.filename)
            self.path_stack.append(self.current_path)
            self.load_remote_directory(new_path)
        else:
            # Open file
            self.open_remote_file(file_info.filename)
            
    def _safe_sftp_operation(self, operation, *args, max_retries: int = 3, **kwargs):
        """Safely execute SFTP operations with error handling
        
        Args:
            operation: SFTP operation to execute
            max_retries: Maximum number of retries
            *args: Arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (OSError, IOError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"SFTP operation failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(1)
                    
        if last_exception:
            raise last_exception
                
    def load_remote_directory(self, path: str):
        """Load remote directory contents
        
        Args:
            path: Remote directory path
        """
        self.file_browser.clear()
        
        try:
            self._safe_sftp_operation(self.sftp.chdir, path)
            self.current_path = self.sftp.getcwd()
            self.path_input.setText(self.current_path)
            
            files = self._safe_sftp_operation(self.sftp.listdir_attr)
            
            # Sort files: directories first, then by name
            sorted_files = sorted(
                files, 
                key=lambda f: (not stat.S_ISDIR(f.st_mode), f.filename.lower())
            )
            
            for file_info in sorted_files:
                is_directory = stat.S_ISDIR(file_info.st_mode)
                name = file_info.filename
                
                # Format size
                size_str = ""
                if not is_directory:
                    size = file_info.st_size
                    for unit in ['B', 'KB', 'MB', 'GB']:
                        if size < 1024:
                            size_str = f"{size:.1f} {unit}"
                            break
                        size /= 1024
                    else:
                        size_str = f"{size:.1f} TB"
                
                item = QTreeWidgetItem([
                    ("📁 " + name) if is_directory else name,
                    size_str,
                    "Folder" if is_directory else "File",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_info.st_mtime))
                ])
                item.setData(0, Qt.UserRole, file_info)
                self.file_browser.addTopLevelItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "SFTP Error", f"Failed to load directory:\n{str(e)}")
            
    def open_remote_file(self, filename: str):
        """Open a remote file for editing
        
        Args:
            filename: Remote filename
        """
        remote_path = posixpath.join(self.current_path, filename)
        
        try:
            # Check file size before downloading
            file_stat = self._safe_sftp_operation(self.sftp.stat, remote_path)
            file_size = file_stat.st_size
            
            # Warn about large files
            if file_size > 10 * 1024 * 1024:  # 10MB
                reply = QMessageBox.question(
                    self, "Large File Warning",
                    f"File {filename} is {file_size / (1024*1024):.1f}MB. "
                    f"Opening large files may be slow. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                    
            # Download to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix="_" + filename) as tmp:
                try:
                    self._safe_sftp_operation(self.sftp.get, remote_path, tmp.name)
                    subprocess.Popen([self.editor_combo.currentText(), tmp.name])
                    
                    # Start file watcher
                    def upload_changes(local_path):
                        try:
                            self._safe_sftp_operation(self.sftp.put, local_path, remote_path)
                            print(f"Auto-uploaded changes to {remote_path}")
                        except Exception as e:
                            print(f"Failed to auto-upload {remote_path}: {e}")
                            
                    FileWatcher(tmp.name, upload_changes).start()
                    
                except Exception as e:
                    os.unlink(tmp.name)  # Clean up temp file on error
                    raise e
                    
        except Exception as e:
            QMessageBox.critical(
                self, "Open File Error",
                f"Failed to open {filename}:\n{str(e)}\n\n"
                f"This could be due to:\n"
                f"• File permissions\n"
                f"• File being locked or in use\n"
                f"• Network connectivity issues"
            )
            
    def upload_file(self, local_path: str, remote_filename: str):
        """Upload a file to the remote server
        
        Args:
            local_path: Local file path
            remote_filename: Remote filename
        """
        try:
            remote_path = posixpath.join(self.current_path, remote_filename)
            
            # Show progress dialog for large files
            file_size = os.path.getsize(local_path)
            if file_size > 1024 * 1024:  # Show progress for files > 1MB
                progress = QProgressDialog(f"Uploading {remote_filename}...", "Cancel", 0, 100, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                
                def progress_callback(transferred, total):
                    if progress.wasCanceled():
                        return False
                    percent = int((transferred / total) * 100)
                    progress.setValue(percent)
                    QApplication.processEvents()
                    return True
                    
                self._safe_sftp_operation(self.sftp.put, local_path, remote_path, callback=progress_callback)
                progress.close()
            else:
                self._safe_sftp_operation(self.sftp.put, local_path, remote_path)
                
            self.load_remote_directory(self.current_path)
            QMessageBox.information(self, "Success", f"Uploaded {remote_filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Upload Error", f"Failed to upload {remote_filename}:\n{str(e)}")
            
    def download_file(self, remote_filename: str, local_path: Optional[str] = None):
        """Download a file from the remote server
        
        Args:
            remote_filename: Remote filename
            local_path: Local file path (optional)
        """
        try:
            remote_path = posixpath.join(self.current_path, remote_filename)
            
            if local_path is None:
                local_path, _ = QFileDialog.getSaveFileName(
                    self, f"Save {remote_filename}", remote_filename
                )
                if not local_path:
                    return
                    
            # Check file size and show progress for large files
            try:
                file_stat = self._safe_sftp_operation(self.sftp.stat, remote_path)
                file_size = file_stat.st_size
                
                if file_size > 1024 * 1024:  # Show progress for files > 1MB
                    progress = QProgressDialog(f"Downloading {remote_filename}...", "Cancel", 0, 100, self)
                    progress.setWindowModality(Qt.WindowModal)
                    progress.show()
                    
                    def progress_callback(transferred, total):
                        if progress.wasCanceled():
                            return False
                        percent = int((transferred / total) * 100)
                        progress.setValue(percent)
                        QApplication.processEvents()
                        return True
                        
                    self._safe_sftp_operation(self.sftp.get, remote_path, local_path, callback=progress_callback)
                    progress.close()
                else:
                    self._safe_sftp_operation(self.sftp.get, remote_path, local_path)
                    
                QMessageBox.information(self, "Success", f"Downloaded {remote_filename}")
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Download Error",
                    f"Failed to download {remote_filename}:\n{str(e)}\n\n"
                    f"This could be due to:\n"
                    f"• File permissions\n"
                    f"• Network connectivity issues\n"
                    f"• File being locked or in use\n"
                    f"• Insufficient disk space"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Download Error", f"Failed to download {remote_filename}:\n{str(e)}")
            
    def go_back(self):
        """Go back to previous directory"""
        if self.path_stack:
            self.load_remote_directory(self.path_stack.pop())
            
    def go_up(self):
        """Go to parent directory"""
        parent_path = posixpath.dirname(self.current_path)
        if parent_path != self.current_path:  # Avoid infinite loop at root
            self.path_stack.append(self.current_path)
            self.load_remote_directory(parent_path)
        
    def go_to_path(self):
        """Navigate to path in input field"""
        self.load_remote_directory(self.path_input.text())
        
    def _show_context_menu(self, position):
        """Show context menu"""
        item = self.file_browser.itemAt(position)
        menu = QMenu(self)
        
        if item:
            file_info = item.data(0, Qt.UserRole)
            
            if not stat.S_ISDIR(file_info.st_mode):
                menu.addAction("Open", lambda: self.open_remote_file(file_info.filename))
                menu.addAction("Download", lambda: self.download_file(file_info.filename))
                
            menu.addAction("Delete", lambda: self._delete(file_info))
            menu.addAction("Rename", lambda: self._rename(file_info))
            menu.addSeparator()
            
        menu.addAction("New File", self._create_remote_file)
        menu.addAction("New Folder", self._create_remote_folder)
        menu.addAction("Upload File", self._upload_file_dialog)
        menu.addAction("Refresh", lambda: self.load_remote_directory(self.current_path))
        
        menu.exec(self.file_browser.viewport().mapToGlobal(position))
        
    def _upload_file_dialog(self):
        """Show file dialog to upload a file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to upload")
        if file_path:
            filename = os.path.basename(file_path)
            self.upload_file(file_path, filename)
            
    def _delete(self, file_info):
        """Delete file or directory"""
        reply = QMessageBox.question(
            self, "Delete",
            f"Delete '{file_info.filename}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                path = posixpath.join(self.current_path, file_info.filename)
                if stat.S_ISDIR(file_info.st_mode):
                    self._safe_sftp_operation(self.sftp.rmdir, path)
                else:
                    self._safe_sftp_operation(self.sftp.remove, path)
                self.load_remote_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete {file_info.filename}:\n{str(e)}")
                
    def _rename(self, file_info):
        """Rename file or directory"""
        new_name, ok = QInputDialog.getText(
            self, "Rename",
            f"New name for '{file_info.filename}':",
            text=file_info.filename
        )
        
        if ok and new_name and new_name != file_info.filename:
            try:
                old_path = posixpath.join(self.current_path, file_info.filename)
                new_path = posixpath.join(self.current_path, new_name)
                self._safe_sftp_operation(self.sftp.rename, old_path, new_path)
                self.load_remote_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", f"Failed to rename {file_info.filename}:\n{str(e)}")
                
    def _create_remote_file(self):
        """Create new remote file"""
        filename, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and filename:
            try:
                remote_path = posixpath.join(self.current_path, filename)
                file_handle = self._safe_sftp_operation(self.sftp.open, remote_path, "w")
                file_handle.close()
                self.load_remote_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Create File Error", f"Failed to create {filename}:\n{str(e)}")
                
    def _create_remote_folder(self):
        """Create new remote folder"""
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and folder_name:
            try:
                remote_path = posixpath.join(self.current_path, folder_name)
                self._safe_sftp_operation(self.sftp.mkdir, remote_path)
                self.load_remote_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Create Folder Error", f"Failed to create folder {folder_name}:\n{str(e)}")
