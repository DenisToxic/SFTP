"""Remote file browser widget"""
import os
import stat
import posixpath
import tempfile
import time
import shutil
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMessageBox, QAbstractItemView,
    QProgressDialog, QApplication
)
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtGui import QDrag
from PySide6.QtCore import QMimeData


class DownloadThread(QThread):
    """Background thread for downloading files/folders"""
    
    progress_updated = Signal(int, int)  # current, total
    download_completed = Signal(list)  # list of local paths
    download_failed = Signal(str)  # error message
    
    def __init__(self, manager, items_to_download, temp_dir):
        """Initialize download thread
        
        Args:
            manager: SFTP manager instance
            items_to_download: List of (remote_path, local_path, is_directory) tuples
            temp_dir: Temporary directory for downloads
        """
        super().__init__()
        self.manager = manager
        self.items_to_download = items_to_download
        self.temp_dir = temp_dir
        self.cancelled = False
        
    def run(self):
        """Download files and folders"""
        try:
            downloaded_paths = []
            total_items = len(self.items_to_download)
            
            for i, (remote_path, local_path, is_directory, filename) in enumerate(self.items_to_download):
                if self.cancelled:
                    break
                    
                self.progress_updated.emit(i, total_items)
                
                if is_directory:
                    # Download folder recursively
                    success = self._download_folder_recursive(remote_path, local_path)
                    if success:
                        downloaded_paths.append(local_path)
                else:
                    # Download single file
                    try:
                        self.manager._safe_sftp_operation(self.manager.sftp.get, remote_path, local_path)
                        downloaded_paths.append(local_path)
                    except Exception as e:
                        self.download_failed.emit(f"Failed to download {filename}: {str(e)}")
                        continue
                        
            self.progress_updated.emit(total_items, total_items)
            self.download_completed.emit(downloaded_paths)
            
        except Exception as e:
            self.download_failed.emit(f"Download failed: {str(e)}")
            
    def _download_folder_recursive(self, remote_folder, local_folder):
        """Download folder recursively
        
        Args:
            remote_folder: Remote folder path
            local_folder: Local folder path
            
        Returns:
            bool: True if successful
        """
        try:
            # Create local directory
            os.makedirs(local_folder, exist_ok=True)
            
            # List remote directory contents
            files = self.manager._safe_sftp_operation(self.manager.sftp.listdir_attr, remote_folder)
            
            for file_info in files:
                if self.cancelled:
                    return False
                    
                remote_item_path = posixpath.join(remote_folder, file_info.filename)
                local_item_path = os.path.join(local_folder, file_info.filename)
                
                if stat.S_ISDIR(file_info.st_mode):
                    # Recursively download subdirectory
                    if not self._download_folder_recursive(remote_item_path, local_item_path):
                        return False
                else:
                    # Download file
                    try:
                        self.manager._safe_sftp_operation(self.manager.sftp.get, remote_item_path, local_item_path)
                    except Exception as e:
                        print(f"Failed to download {file_info.filename}: {e}")
                        # Continue with other files
                        
            return True
            
        except Exception as e:
            print(f"Failed to download folder {remote_folder}: {e}")
            return False
            
    def cancel(self):
        """Cancel download"""
        self.cancelled = True


class RemoteFileBrowser(QTreeWidget):
    """Tree widget for browsing remote files with drag/drop support"""
    
    def __init__(self, manager):
        """Initialize remote file browser
        
        Args:
            manager: SFTP manager instance
        """
        super().__init__()
        self.manager = manager
        self.download_thread = None
        self.progress_dialog = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface"""
        self.setColumnCount(4)
        self.setHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
    def supportedDragActions(self):
        """Supported drag actions"""
        return Qt.CopyAction
        
    def supportedDropActions(self):
        """Supported drop actions"""
        return Qt.CopyAction
        
    def startDrag(self, _):
        """Start drag operation - download selected items to temp location"""
        items = self.selectedItems()
        if not items:
            return
            
        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp(prefix="sftp-download-")
        
        # Prepare items for download
        items_to_download = []
        for item in items:
            file_info = item.data(0, Qt.UserRole)
            remote_path = posixpath.join(self.manager.current_path, file_info.filename)
            local_path = os.path.join(temp_dir, file_info.filename)
            is_directory = stat.S_ISDIR(file_info.st_mode)
            
            items_to_download.append((remote_path, local_path, is_directory, file_info.filename))
        
        # Show progress dialog
        self.progress_dialog = QProgressDialog(
            "Preparing files for download...", "Cancel", 0, len(items_to_download), self
        )
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Download Progress")
        self.progress_dialog.show()
        
        # Start download thread
        self.download_thread = DownloadThread(self.manager, items_to_download, temp_dir)
        self.download_thread.progress_updated.connect(self._on_download_progress)
        self.download_thread.download_completed.connect(self._on_download_completed)
        self.download_thread.download_failed.connect(self._on_download_failed)
        self.progress_dialog.canceled.connect(self.download_thread.cancel)
        
        self.download_thread.start()
        
    def _on_download_progress(self, current, total):
        """Handle download progress update"""
        if self.progress_dialog:
            self.progress_dialog.setValue(current)
            self.progress_dialog.setLabelText(f"Downloaded {current} of {total} items...")
            
    def _on_download_completed(self, downloaded_paths):
        """Handle download completion"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        if downloaded_paths:
            # Create URLs for downloaded files
            urls = [QUrl.fromLocalFile(path) for path in downloaded_paths]
            
            # Create drag operation
            mime_data = QMimeData()
            mime_data.setUrls(urls)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.CopyAction)
        else:
            QMessageBox.warning(self, "Download Failed", "No files were successfully downloaded.")
            
    def _on_download_failed(self, error_message):
        """Handle download failure"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
            
        QMessageBox.critical(self, "Download Error", error_message)
            
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
            
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
            
    def dropEvent(self, event):
        """Handle drop event - upload files/folders to remote server"""
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            
            if os.path.isfile(local_path):
                # Handle file upload
                filename = os.path.basename(local_path)
                remote_path = posixpath.join(self.manager.current_path, filename)
                
                try:
                    # Check if file exists
                    self.manager.sftp.stat(remote_path)
                    reply = QMessageBox.question(
                        self, "Replace File",
                        f"'{filename}' already exists. Replace it?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        continue
                except IOError:
                    # File doesn't exist, proceed with upload
                    pass
                    
                self.manager.upload_file(local_path, filename)
                
            elif os.path.isdir(local_path):
                # Handle folder upload
                folder_name = os.path.basename(local_path)
                remote_folder_path = posixpath.join(self.manager.current_path, folder_name)
                
                try:
                    # Check if folder exists
                    self.manager.sftp.stat(remote_folder_path)
                    reply = QMessageBox.question(
                        self, "Folder Exists",
                        f"Folder '{folder_name}' already exists. Merge contents?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        continue
                except IOError:
                    # Folder doesn't exist, proceed with upload
                    pass
                    
                # Upload folder
                self.manager.upload_folder(local_path, folder_name)
                
        event.acceptProposedAction()
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Delete:
            selected_items = self.selectedItems()
            if selected_items:
                file_info = selected_items[0].data(0, Qt.UserRole)
                self.manager._delete(file_info)
        else:
            super().keyPressEvent(event)
