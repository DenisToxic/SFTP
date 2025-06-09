"""File browser widget for SFTP operations"""
import os
import stat
import posixpath
import tempfile
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QMenu, QInputDialog,
    QFileDialog, QProgressDialog, QApplication, QAbstractItemView,
    QGroupBox, QComboBox, QLabel
)
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtGui import QDrag
from PySide6.QtCore import QMimeData
import subprocess

from core.file_manager import FileManager
from utils.file_watcher import FileWatcher


class FileBrowserWidget(QWidget):
    """Widget for browsing and managing remote files"""
    
    def __init__(self, file_manager: FileManager):
        """Initialize file browser widget
        
        Args:
            file_manager: File manager instance
        """
        super().__init__()
        self.file_manager = file_manager
        self._setup_ui()
        self._setup_connections()
        self.refresh()
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        
        # Navigation bar
        nav_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("⬅ Back")
        self.back_btn.clicked.connect(self._go_back)
        
        self.up_btn = QPushButton("⬆ Up")
        self.up_btn.clicked.connect(self._go_up)
        
        self.path_input = QLineEdit()
        self.path_input.returnPressed.connect(self._go_to_path)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.up_btn)
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
        
        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.setAcceptDrops(True)
        self.file_tree.setDragEnabled(True)
        self.file_tree.setDropIndicatorShown(True)
        self.file_tree.setDragDropMode(QAbstractItemView.DragDrop)
        
        # Connect signals
        self.file_tree.itemDoubleClicked.connect(self._handle_double_click)
        self.file_tree.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.file_tree)
        
    def _setup_connections(self):
        """Setup signal connections"""
        self.file_manager.directory_changed.connect(self._on_directory_changed)
        self.file_manager.file_uploaded.connect(self._on_file_uploaded)
        self.file_manager.file_downloaded.connect(self._on_file_downloaded)
        
    def refresh(self):
        """Refresh file listing"""
        try:
            files = self.file_manager.list_directory()
            self._populate_tree(files)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh directory: {e}")
            
    def _populate_tree(self, files):
        """Populate tree with file list
        
        Args:
            files: List of RemoteFileInfo objects
        """
        self.file_tree.clear()
        
        for file_info in files:
            item = QTreeWidgetItem([
                ("📁 " + file_info.filename) if file_info.is_directory else file_info.filename,
                file_info.size_formatted,
                "Folder" if file_info.is_directory else "File",
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_info.modified_time))
            ])
            item.setData(0, Qt.UserRole, file_info)
            self.file_tree.addTopLevelItem(item)
            
    def _handle_double_click(self, item, column):
        """Handle double-click on item"""
        file_info = item.data(0, Qt.UserRole)
        
        if file_info.is_directory:
            # Navigate into directory
            self.file_manager.change_directory(
                posixpath.join(self.file_manager.current_path, file_info.filename)
            )
        else:
            # Open file for editing
            self._open_file(file_info.filename)
            
    def _go_back(self):
        """Go back to previous directory"""
        if self.file_manager.go_back():
            self.refresh()
            
    def _go_up(self):
        """Go to parent directory"""
        self.file_manager.go_up()
        self.refresh()
        
    def _go_to_path(self):
        """Navigate to path in input field"""
        path = self.path_input.text()
        try:
            self.file_manager.change_directory(path)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to navigate to {path}: {e}")
            
    def _on_directory_changed(self, path: str):
        """Handle directory change"""
        self.path_input.setText(path)
        
    def _on_file_uploaded(self, filename: str):
        """Handle file upload"""
        self.refresh()
        
    def _on_file_downloaded(self, filename: str):
        """Handle file download"""
        pass  # No need to refresh for downloads
        
    def upload_file(self, local_path: str):
        """Upload a file
        
        Args:
            local_path: Local file path
        """
        try:
            filename = os.path.basename(local_path)
            
            # Show progress for large files
            file_size = os.path.getsize(local_path)
            if file_size > 1024 * 1024:  # 1MB
                progress = QProgressDialog(f"Uploading {filename}...", "Cancel", 0, 100, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.show()
                
                def progress_callback(transferred, total):
                    if progress.wasCanceled():
                        return False
                    percent = int((transferred / total) * 100)
                    progress.setValue(percent)
                    QApplication.processEvents()
                    return True
                
                self.file_manager.upload_file(local_path, filename, progress_callback)
                progress.close()
            else:
                self.file_manager.upload_file(local_path, filename)
                
        except Exception as e:
            QMessageBox.critical(self, "Upload Error", f"Failed to upload {filename}: {e}")
            
    def download_selected_file(self):
        """Download selected file"""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", "No file selected")
            return
            
        file_info = selected_items[0].data(0, Qt.UserRole)
        if file_info.is_directory:
            QMessageBox.information(self, "Info", "Cannot download directories")
            return
            
        # Get save location
        local_path, _ = QFileDialog.getSaveFileName(
            self, f"Save {file_info.filename}", file_info.filename
        )
        
        if local_path:
            try:
                # Show progress for large files
                if file_info.size > 1024 * 1024:  # 1MB
                    progress = QProgressDialog(f"Downloading {file_info.filename}...", "Cancel", 0, 100, self)
                    progress.setWindowModality(Qt.WindowModal)
                    progress.show()
                    
                    def progress_callback(transferred, total):
                        if progress.wasCanceled():
                            return False
                        percent = int((transferred / total) * 100)
                        progress.setValue(percent)
                        QApplication.processEvents()
                        return True
                    
                    self.file_manager.download_file(file_info.filename, local_path, progress_callback)
                    progress.close()
                else:
                    self.file_manager.download_file(file_info.filename, local_path)
                    
                QMessageBox.information(self, "Success", f"Downloaded {file_info.filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Download Error", f"Failed to download {file_info.filename}: {e}")
                
    def _open_file(self, filename: str):
        """Open file for editing
        
        Args:
            filename: Remote filename
        """
        try:
            # Get temporary file
            temp_path = self.file_manager.get_file_for_editing(filename)
            
            # Open with editor
            editor = self.editor_combo.currentText()
            subprocess.Popen([editor, temp_path])
            
            # Watch for changes
            def upload_changes(local_path):
                try:
                    self.file_manager.upload_edited_file(local_path, filename)
                    print(f"Auto-uploaded changes to {filename}")
                except Exception as e:
                    print(f"Failed to auto-upload {filename}: {e}")
                    
            FileWatcher(temp_path, upload_changes).start()
            
        except Exception as e:
            QMessageBox.critical(self, "Open File Error", f"Failed to open {filename}: {e}")
            
    def _show_context_menu(self, pos):
        """Show context menu"""
        item = self.file_tree.itemAt(pos)
        menu = QMenu(self)
        
        if item:
            file_info = item.data(0, Qt.UserRole)
            
            if not file_info.is_directory:
                menu.addAction("Open", lambda: self._open_file(file_info.filename))
                menu.addAction("Download", lambda: self._download_file(file_info.filename))
            
            menu.addAction("Delete", lambda: self._delete_file(file_info))
            menu.addAction("Rename", lambda: self._rename_file(file_info))
            
        menu.addSeparator()
        menu.addAction("New File", self._create_file)
        menu.addAction("New Folder", self._create_folder)
        menu.addAction("Upload File", self._upload_file_dialog)
        
        menu.exec(self.file_tree.viewport().mapToGlobal(pos))
        
    def _download_file(self, filename: str):
        """Download specific file"""
        local_path, _ = QFileDialog.getSaveFileName(self, f"Save {filename}", filename)
        if local_path:
            try:
                self.file_manager.download_file(filename, local_path)
                QMessageBox.information(self, "Success", f"Downloaded {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Download Error", f"Failed to download {filename}: {e}")
                
    def _delete_file(self, file_info):
        """Delete file or directory"""
        reply = QMessageBox.question(
            self, "Delete", 
            f"Are you sure you want to delete '{file_info.filename}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.file_manager.delete_file(file_info.filename)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete {file_info.filename}: {e}")
                
    def _rename_file(self, file_info):
        """Rename file or directory"""
        new_name, ok = QInputDialog.getText(
            self, "Rename", 
            f"New name for '{file_info.filename}':",
            text=file_info.filename
        )
        
        if ok and new_name and new_name != file_info.filename:
            try:
                self.file_manager.rename_file(file_info.filename, new_name)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", f"Failed to rename {file_info.filename}: {e}")
                
    def _create_file(self):
        """Create new file"""
        filename, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and filename:
            try:
                self.file_manager.create_file(filename)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Create File Error", f"Failed to create {filename}: {e}")
                
    def _create_folder(self):
        """Create new folder"""
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and folder_name:
            try:
                self.file_manager.create_directory(folder_name)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Create Folder Error", f"Failed to create folder {folder_name}: {e}")
                
    def _upload_file_dialog(self):
        """Show file upload dialog"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file to upload")
        if file_path:
            self.upload_file(file_path)
            
    # Drag and drop support
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
        """Handle drop event"""
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if os.path.isfile(local_path):
                self.upload_file(local_path)
                
        event.acceptProposedAction()
