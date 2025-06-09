"""Legacy SFTP GUI Manager implementation (moved from main.py)"""
import os
import stat
import posixpath
import time
import tempfile
import subprocess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QGroupBox, QComboBox, QLabel, QMessageBox, QMenu, QInputDialog,
    QFileDialog, QProgressDialog, QApplication, QToolBar, QSplitter
)
from PySide6.QtCore import Qt
import paramiko

from ui.widgets.legacy_terminal_widget import LegacyTerminalWidget
from ui.widgets.legacy_file_browser import LegacyRemoteFileBrowser
from utils.file_watcher import FileWatcher


class LegacySftpGuiManager(QMainWindow):
    """Legacy SFTP GUI Manager implementation"""
    
    def __init__(self, ssh, sftp, host, port, user, password, version_manager):
        """Initialize legacy SFTP manager
        
        Args:
            ssh: SSH client
            sftp: SFTP client
            host: SSH hostname
            port: SSH port
            user: SSH username
            password: SSH password
            version_manager: Version manager instance
        """
        super().__init__()
        self.ssh, self.sftp = ssh, sftp
        self.host, self.port = host, port
        self.user, self.pw = user, password
        self.path_stack = []
        self.current_path = "."
        self.version_manager = version_manager
        
        self.setWindowTitle("SFTP GUI Manager")
        self.resize(1200, 700)
        
        self._setup_ui()
        self.load_remote_directory(".")
        
    def _setup_ui(self):
        """Setup user interface"""
        # Create toolbar
        toolbar = QToolBar("Actions")
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        toolbar.addAction("Refresh", lambda: self.load_remote_directory(self.current_path))
        
        # Create main splitter
        splitter = QSplitter()
        splitter.addWidget(LegacyTerminalWidget(self.host, self.port, self.user, self.pw))
        splitter.addWidget(self._create_browser_widget())
        splitter.setSizes([700, 500])
        self.setCentralWidget(splitter)
        
    def _create_browser_widget(self):
        """Create file browser widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Navigation bar
        nav_layout = QHBoxLayout()
        
        back_btn = QPushButton("⬅ Back")
        back_btn.clicked.connect(self.go_back)
        
        up_btn = QPushButton("⬆ Up")
        up_btn.clicked.connect(self.go_up)
        
        self.path_input = QLineEdit()
        self.path_input.returnPressed.connect(self.go_to)
        
        nav_layout.addWidget(back_btn)
        nav_layout.addWidget(up_btn)
        nav_layout.addWidget(self.path_input)
        
        layout.addLayout(nav_layout)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        settings_layout.addWidget(QLabel("Default Editor:"))
        self.editor = QComboBox()
        self.editor.addItems(["notepad.exe", "code", "notepad++", "gedit"])
        settings_layout.addWidget(self.editor)
        
        layout.addWidget(settings_group)
        
        # File browser
        self.fb = LegacyRemoteFileBrowser(self)
        self.fb.itemDoubleClicked.connect(self._handle_double_click)
        self.fb.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.fb)
        
        return widget
        
    def _handle_double_click(self, item, column):
        """Handle double-click on file browser items"""
        file_info = item.data(0, Qt.UserRole)
        
        if stat.S_ISDIR(file_info.st_mode):
            # If it's a directory, navigate into it
            new_path = posixpath.join(self.current_path, file_info.filename)
            self.path_stack.append(self.current_path)
            self.load_remote_directory(new_path)
        else:
            # If it's a file, try to open it
            self.open_remote_file(file_info.filename)
            
    def _safe_sftp_operation(self, operation, *args, **kwargs):
        """Safely execute SFTP operations with error handling"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (OSError, IOError, paramiko.SSHException) as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"SFTP operation failed (attempt {attempt + 1}), retrying: {e}")
                time.sleep(1)  # Wait before retry
                
    def upload_file(self, local_path, remote_filename):
        """Upload a file to the remote server"""
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
            
    def download_file(self, remote_filename, local_path=None):
        """Download a file from the remote server"""
        try:
            remote_path = posixpath.join(self.current_path, remote_filename)
            
            if local_path is None:
                local_path, _ = QFileDialog.getSaveFileName(
                    self, f"Save {remote_filename}", remote_filename
                )
                if not local_path:
                    return
            
            # Check if file exists and get size for progress
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
                QMessageBox.critical(self, "Download Error", 
                    f"Failed to download {remote_filename}:\n{str(e)}\n\n"
                    f"This could be due to:\n"
                    f"• File permissions\n"
                    f"• Network connectivity issues\n"
                    f"• File being locked or in use\n"
                    f"• Insufficient disk space")
                
        except Exception as e:
            QMessageBox.critical(self, "Download Error", f"Failed to download {remote_filename}:\n{str(e)}")
            
    def load_remote_directory(self, path):
        """Load remote directory contents"""
        self.fb.clear()
        try:
            self._safe_sftp_operation(self.sftp.chdir, path)
            self.current_path = self.sftp.getcwd()
            self.path_input.setText(self.current_path)
            
            files = self._safe_sftp_operation(self.sftp.listdir_attr)
            for file_info in files:
                is_directory = stat.S_ISDIR(file_info.st_mode)
                name = file_info.filename
                
                item = QTreeWidgetItem([
                    ("📁 " + name) if is_directory else name,
                    "" if is_directory else f"{file_info.st_size} B",
                    "Folder" if is_directory else "File",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_info.st_mtime))
                ])
                item.setData(0, Qt.UserRole, file_info)
                self.fb.addTopLevelItem(item)
        except Exception as e:
            QMessageBox.critical(self, "SFTP Error", f"Failed to load directory:\n{str(e)}")
            
    def open_remote_file(self, filename):
        """Open a remote file for editing"""
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
            
            with tempfile.NamedTemporaryFile(delete=False, suffix="_" + filename) as tmp:
                try:
                    self._safe_sftp_operation(self.sftp.get, remote_path, tmp.name)
                    subprocess.Popen([self.editor.currentText(), tmp.name])
                    FileWatcher(tmp.name, lambda lp: self._upload_changed_file(lp, remote_path)).start()
                except Exception as e:
                    os.unlink(tmp.name)  # Clean up temp file on error
                    raise e
                    
        except Exception as e:
            QMessageBox.critical(self, "Open File Error", 
                f"Failed to open {filename}:\n{str(e)}\n\n"
                f"This could be due to:\n"
                f"• File permissions\n"
                f"• File being locked or in use\n"
                f"• Network connectivity issues")
                
    def _upload_changed_file(self, local_path, remote_path):
        """Upload a changed file back to the server"""
        try:
            self._safe_sftp_operation(self.sftp.put, local_path, remote_path)
            print(f"Auto-uploaded changes to {remote_path}")
        except Exception as e:
            print(f"Failed to auto-upload {remote_path}: {e}")
            
    def go_back(self):
        """Go back to previous directory"""
        if self.path_stack:
            self.load_remote_directory(self.path_stack.pop())
            
    def go_up(self):
        """Go to parent directory"""
        self.path_stack.append(self.current_path)
        self.load_remote_directory(posixpath.dirname(self.current_path))
        
    def go_to(self):
        """Navigate to path in input field"""
        self.load_remote_directory(self.path_input.text())
        
    def _show_context_menu(self, pos):
        """Show context menu"""
        item = self.fb.itemAt(pos)
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
        menu.exec(self.fb.viewport().mapToGlobal(pos))
        
    def _upload_file_dialog(self):
        """Show file dialog to upload a file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to upload")
        if file_path:
            filename = os.path.basename(file_path)
            self.upload_file(file_path, filename)
            
    def _delete(self, file_info):
        """Delete file or directory"""
        if QMessageBox.question(self, "Delete", f"Delete '{file_info.filename}'?") == QMessageBox.Yes:
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
        new_name, ok = QInputDialog.getText(self, "Rename", f"New name for '{file_info.filename}':")
        if ok and new_name:
            try:
                self._safe_sftp_operation(
                    self.sftp.rename,
                    posixpath.join(self.current_path, file_info.filename),
                    posixpath.join(self.current_path, new_name)
                )
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
                self._safe_sftp_operation(self.sftp.mkdir, posixpath.join(self.current_path, folder_name))
                self.load_remote_directory(self.current_path)
            except Exception as e:
                QMessageBox.critical(self, "Create Folder Error", f"Failed to create folder {folder_name}:\n{str(e)}")
