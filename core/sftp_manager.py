"""SFTP Manager implementation"""
import os
import stat
import posixpath
import time
import tempfile
import subprocess
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QGroupBox, QComboBox, QLabel, QMessageBox, QMenu, QInputDialog,
    QFileDialog, QProgressDialog, QApplication, QTreeWidgetItem
)
from PySide6.QtCore import Qt
import paramiko

from ui.widgets.remote_file_browser import RemoteFileBrowser
from utils.file_watcher import FileWatcher


class SftpManager(QWidget):
    """SFTP Manager widget"""
    
    def __init__(self, ssh, sftp, host, port, user, password):
        """Initialize SFTP manager
        
        Args:
            ssh: SSH client
            sftp: SFTP client
            host: SSH hostname
            port: SSH port
            user: SSH username
            password: SSH password
        """
        super().__init__()
        self.ssh, self.sftp = ssh, sftp
        self.host, self.port = host, port
        self.user, self.pw = user, password
        self.path_stack = []
        self.current_path = "."
        
        self._setup_ui()
        self.load_remote_directory(".")
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
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
        self.file_browser = RemoteFileBrowser(self)
        self.file_browser.itemDoubleClicked.connect(self._handle_double_click)
        self.file_browser.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.file_browser)
        
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
            
    def upload_folder(self, local_folder_path, remote_folder_name):
        """Upload an entire folder recursively
        
        Args:
            local_folder_path: Local folder path
            remote_folder_name: Remote folder name
        """
        try:
            remote_folder_path = posixpath.join(self.current_path, remote_folder_name)
            
            # Count total files for progress tracking
            total_files = 0
            for root, dirs, files in os.walk(local_folder_path):
                total_files += len(files)
            
            if total_files == 0:
                # Create empty directory
                try:
                    self._safe_sftp_operation(self.sftp.mkdir, remote_folder_path)
                except IOError:
                    # Directory might already exist
                    pass
                    
                QMessageBox.information(self, "Empty Folder", f"Created empty folder '{remote_folder_name}'")
                self.load_remote_directory(self.current_path)
                return
            
            # Show progress dialog for folder upload
            progress = QProgressDialog(f"Uploading folder '{remote_folder_name}'...", "Cancel", 0, total_files, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Folder Upload")
            progress.show()
            
            uploaded_files = 0
            cancelled = False
            
            def upload_recursive(local_dir, remote_dir):
                nonlocal uploaded_files, cancelled
                
                if cancelled:
                    return False
                
                # Create remote directory if it doesn't exist
                try:
                    try:
                        self.sftp.stat(remote_dir)
                    except IOError:
                        self._safe_sftp_operation(self.sftp.mkdir, remote_dir)
                except Exception as e:
                    print(f"Failed to create directory {remote_dir}: {e}")
                    return False
                
                # Upload files and subdirectories
                for item in os.listdir(local_dir):
                    if progress.wasCanceled():
                        cancelled = True
                        return False
                        
                    local_item_path = os.path.join(local_dir, item)
                    remote_item_path = posixpath.join(remote_dir, item)
                    
                    if os.path.isfile(local_item_path):
                        # Upload file
                        try:
                            self._safe_sftp_operation(self.sftp.put, local_item_path, remote_item_path)
                            uploaded_files += 1
                            progress.setValue(uploaded_files)
                            progress.setLabelText(f"Uploading: {item} ({uploaded_files}/{total_files})")
                            QApplication.processEvents()
                        except Exception as e:
                            QMessageBox.warning(
                                self, "Upload Error", 
                                f"Failed to upload {item}:\n{str(e)}"
                            )
                            # Continue with other files
                            
                    elif os.path.isdir(local_item_path):
                        # Recursively upload subdirectory
                        if not upload_recursive(local_item_path, remote_item_path):
                            return False
                
                return True
            
            # Start recursive upload
            success = upload_recursive(local_folder_path, remote_folder_path)
            progress.close()
            
            if success and not cancelled:
                self.load_remote_directory(self.current_path)
                QMessageBox.information(
                    self, "Success", 
                    f"Folder '{remote_folder_name}' uploaded successfully!\n"
                    f"Uploaded {uploaded_files} files."
                )
            elif cancelled:
                QMessageBox.information(
                    self, "Cancelled", 
                    f"Folder upload cancelled. {uploaded_files} files were uploaded."
                )
                self.load_remote_directory(self.current_path)
                
        except Exception as e:
            QMessageBox.critical(
                self, "Folder Upload Error", 
                f"Failed to upload folder '{remote_folder_name}':\n{str(e)}"
            )
            
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
            
    def download_folder(self, remote_folder_name, local_folder_path=None):
        """Download an entire folder recursively
        
        Args:
            remote_folder_name: Remote folder name
            local_folder_path: Local folder path (optional)
        """
        try:
            remote_folder_path = posixpath.join(self.current_path, remote_folder_name)
            
            if local_folder_path is None:
                local_folder_path = QFileDialog.getExistingDirectory(
                    self, f"Save folder '{remote_folder_name}' to...", ""
                )
                if not local_folder_path:
                    return
                    
                local_folder_path = os.path.join(local_folder_path, remote_folder_name)
            
            # Count total files for progress tracking
            def count_remote_files(remote_dir):
                count = 0
                try:
                    files = self._safe_sftp_operation(self.sftp.listdir_attr, remote_dir)
                    for file_info in files:
                        if stat.S_ISDIR(file_info.st_mode):
                            count += count_remote_files(posixpath.join(remote_dir, file_info.filename))
                        else:
                            count += 1
                except Exception:
                    pass
                return count
            
            total_files = count_remote_files(remote_folder_path)
            
            if total_files == 0:
                # Create empty directory
                os.makedirs(local_folder_path, exist_ok=True)
                QMessageBox.information(self, "Empty Folder", f"Created empty folder '{remote_folder_name}'")
                return
            
            # Show progress dialog for folder download
            progress = QProgressDialog(f"Downloading folder '{remote_folder_name}'...", "Cancel", 0, total_files, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Folder Download")
            progress.show()
            
            downloaded_files = 0
            cancelled = False
            
            def download_recursive(remote_dir, local_dir):
                nonlocal downloaded_files, cancelled
                
                if cancelled:
                    return False
                
                # Create local directory
                os.makedirs(local_dir, exist_ok=True)
                
                # Download files and subdirectories
                try:
                    files = self._safe_sftp_operation(self.sftp.listdir_attr, remote_dir)
                    
                    for file_info in files:
                        if progress.wasCanceled():
                            cancelled = True
                            return False
                            
                        remote_item_path = posixpath.join(remote_dir, file_info.filename)
                        local_item_path = os.path.join(local_dir, file_info.filename)
                        
                        if stat.S_ISDIR(file_info.st_mode):
                            # Recursively download subdirectory
                            if not download_recursive(remote_item_path, local_item_path):
                                return False
                        else:
                            # Download file
                            try:
                                self._safe_sftp_operation(self.sftp.get, remote_item_path, local_item_path)
                                downloaded_files += 1
                                progress.setValue(downloaded_files)
                                progress.setLabelText(f"Downloading: {file_info.filename} ({downloaded_files}/{total_files})")
                                QApplication.processEvents()
                            except Exception as e:
                                QMessageBox.warning(
                                    self, "Download Error", 
                                    f"Failed to download {file_info.filename}:\n{str(e)}"
                                )
                                # Continue with other files
                                
                except Exception as e:
                    print(f"Failed to list directory {remote_dir}: {e}")
                    return False
                
                return True
            
            # Start recursive download
            success = download_recursive(remote_folder_path, local_folder_path)
            progress.close()
            
            if success and not cancelled:
                QMessageBox.information(
                    self, "Success", 
                    f"Folder '{remote_folder_name}' downloaded successfully!\n"
                    f"Downloaded {downloaded_files} files to:\n{local_folder_path}"
                )
            elif cancelled:
                QMessageBox.information(
                    self, "Cancelled", 
                    f"Folder download cancelled. {downloaded_files} files were downloaded."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Folder Download Error", 
                f"Failed to download folder '{remote_folder_name}':\n{str(e)}"
            )
            
    def load_remote_directory(self, path):
        """Load remote directory contents"""
        self.file_browser.clear()
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
                self.file_browser.addTopLevelItem(item)
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
        item = self.file_browser.itemAt(pos)
        menu = QMenu(self)
        if item:
            file_info = item.data(0, Qt.UserRole)
            if not stat.S_ISDIR(file_info.st_mode):
                menu.addAction("Open", lambda: self.open_remote_file(file_info.filename))
                menu.addAction("Download", lambda: self.download_file(file_info.filename))
            else:
                menu.addAction("Download Folder", lambda: self.download_folder(file_info.filename))
            menu.addAction("Delete", lambda: self._delete(file_info))
            menu.addAction("Rename", lambda: self._rename(file_info))
        menu.addSeparator()
        menu.addAction("New File", self._create_remote_file)
        menu.addAction("New Folder", self._create_remote_folder)
        menu.addAction("Upload File", self._upload_file_dialog)
        menu.exec(self.file_browser.viewport().mapToGlobal(pos))
        
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
