"""Remote file browser widget"""
import os
import stat
import posixpath
import tempfile
import time
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMessageBox, QAbstractItemView
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDrag
from PySide6.QtCore import QMimeData


class RemoteFileBrowser(QTreeWidget):
    """Tree widget for browsing remote files with drag/drop support"""
    
    def __init__(self, manager):
        """Initialize remote file browser
        
        Args:
            manager: SFTP manager instance
        """
        super().__init__()
        self.manager = manager
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
        """Start drag operation"""
        items = self.selectedItems()
        if not items:
            return
            
        temp_dir = tempfile.mkdtemp(prefix="sftp-drag-")
        urls = []
        
        for item in items:
            file_info = item.data(0, Qt.UserRole)
            if not stat.S_ISDIR(file_info.st_mode):
                remote_path = posixpath.join(self.manager.current_path, file_info.filename)
                local_path = os.path.join(temp_dir, file_info.filename)
                
                try:
                    self.manager.sftp.get(remote_path, local_path)
                    urls.append(QUrl.fromLocalFile(local_path))
                except Exception as e:
                    QMessageBox.warning(
                        self, "Drag Error", 
                        f"Could not prepare {file_info.filename}: {str(e)}"
                    )
        
        if urls:
            mime_data = QMimeData()
            mime_data.setUrls(urls)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.CopyAction)
            
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
