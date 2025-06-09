"""Main application window with version control integration"""
import stat
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QToolBar, QStatusBar, QMessageBox, QMenuBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from core.ssh_manager import SSHManager
from core.file_manager import FileManager
from core.version_manager import VersionManager
from ui.widgets.terminal_widget import TerminalWidget
from ui.dialogs.update_dialog import UpdateDialog
from ui.dialogs.about_dialog import AboutDialog
from core.sftp_manager import SftpManager


class MainWindow(QMainWindow):
    """Main application window with version control"""
    
    def __init__(self, ssh_manager: SSHManager, version_manager: VersionManager = None):
        """Initialize main window
        
        Args:
            ssh_manager: SSH manager instance
            version_manager: Version manager instance
        """
        super().__init__()
        self.ssh_manager = ssh_manager
        self.file_manager = FileManager(ssh_manager)
        self.version_manager = version_manager or VersionManager()
        
        self.setWindowTitle(f"SFTP GUI Manager v{self.version_manager.get_current_version()}")
        self.resize(1400, 800)
        
        self._setup_ui()
        self._setup_menu()
        self._setup_connections()
            
    def _setup_ui(self):
        """Setup user interface"""
        # Create toolbar
        self._create_toolbar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Connected to {self.ssh_manager.host}")
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Create terminal widget
        self.terminal_widget = TerminalWidget(
            self.ssh_manager.host,
            self.ssh_manager.port,
            self.ssh_manager.username,
            self.ssh_manager.password
        )
        
        # Create SFTP manager widget
        self.sftp_manager = SftpManager(
            self.ssh_manager.ssh_client,
            self.ssh_manager.sftp_client,
            self.ssh_manager.host,
            self.ssh_manager.port,
            self.ssh_manager.username,
            self.ssh_manager.password
        )
        
        # Add widgets to splitter
        splitter.addWidget(self.terminal_widget)
        splitter.addWidget(self.sftp_manager)
        splitter.setSizes([600, 800])
        
        self.setCentralWidget(splitter)
        
    def _setup_menu(self):
        """Setup application menu"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        connect_action = QAction("New Connection", self)
        connect_action.setShortcut("Ctrl+N")
        connect_action.triggered.connect(self._new_connection)
        file_menu.addAction(connect_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        settings_action = QAction("Update Settings", self)
        settings_action.triggered.connect(self._show_update_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(check_updates_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        
        # Refresh action
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_files)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Upload action
        upload_action = QAction("⬆️ Upload", self)
        upload_action.setShortcut("Ctrl+U")
        upload_action.triggered.connect(self._upload_file)
        toolbar.addAction(upload_action)
        
        # Download action
        download_action = QAction("⬇️ Download", self)
        download_action.setShortcut("Ctrl+D")
        download_action.triggered.connect(self._download_file)
        toolbar.addAction(download_action)
        
        toolbar.addSeparator()
        
        # Disconnect action
        disconnect_action = QAction("🔌 Disconnect", self)
        disconnect_action.triggered.connect(self._disconnect)
        toolbar.addAction(disconnect_action)
        
    def _setup_connections(self):
        """Setup signal connections"""
        # File manager signals
        self.file_manager.directory_changed.connect(self._on_directory_changed)
        self.file_manager.file_uploaded.connect(self._on_file_uploaded)
        self.file_manager.file_downloaded.connect(self._on_file_downloaded)
        
        # SSH manager signals
        self.ssh_manager.connection_lost.connect(self._on_connection_lost)
        
        # Version manager signals
        self.version_manager.update_available.connect(self._on_update_available)
        self.version_manager.update_installed.connect(self._on_update_installed)
        self.version_manager.update_failed.connect(self._on_update_failed)
        
    def _refresh_files(self):
        """Refresh file browser"""
        try:
            self.sftp_manager.load_remote_directory(self.sftp_manager.current_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh: {e}")
            
    def _upload_file(self):
        """Upload file"""
        self.sftp_manager._upload_file_dialog()
        
    def _download_file(self):
        """Download selected file"""
        selected_items = self.sftp_manager.file_browser.selectedItems()
        if selected_items:
            file_info = selected_items[0].data(0, Qt.UserRole)
            if not stat.S_ISDIR(file_info.st_mode):
                self.sftp_manager.download_file(file_info.filename)
            else:
                QMessageBox.information(self, "Info", "Cannot download directories")
        else:
            QMessageBox.information(self, "Info", "No file selected")
        
    def _disconnect(self):
        """Disconnect from server"""
        self.ssh_manager.disconnect()
        self.close()
        
    def _new_connection(self):
        """Create new connection"""
        from ui.dialogs.connection_dialog import ConnectionDialog
        
        dialog = ConnectionDialog()
        if dialog.exec() == dialog.Accepted:
            # Get connection info
            host, port, username, password = dialog.get_connection_info()
            
            # Create new SSH manager and connect
            try:
                new_ssh_manager = SSHManager()
                new_ssh_manager.connect(host, port, username, password)
                
                # Create new main window
                new_window = MainWindow(new_ssh_manager, self.version_manager)
                new_window.show()
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")
            
    def _show_update_settings(self):
        """Show update settings dialog"""
        dialog = UpdateDialog(parent=self)
        dialog.exec()
        
    def _check_for_updates(self):
        """Check for updates manually"""
        self.version_manager.check_for_updates(silent=False)
        
    def _show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def _on_directory_changed(self, path: str):
        """Handle directory change"""
        self.status_bar.showMessage(f"Current directory: {path}")
        
    def _on_file_uploaded(self, filename: str):
        """Handle file upload completion"""
        self.status_bar.showMessage(f"Uploaded: {filename}", 3000)
        self._refresh_files()
        
    def _on_file_downloaded(self, filename: str):
        """Handle file download completion"""
        self.status_bar.showMessage(f"Downloaded: {filename}", 3000)
        
    def _on_connection_lost(self):
        """Handle connection loss"""
        QMessageBox.critical(self, "Connection Lost", "Connection to server was lost.")
        self.close()
        
    def _on_update_available(self, version_info):
        """Handle update available notification"""
        dialog = UpdateDialog(version_info, self)
        dialog.exec()
        
    def _on_update_installed(self):
        """Handle update installation completion"""
        self.status_bar.showMessage("Update installed successfully!", 5000)
        
    def _on_update_failed(self, error_message):
        """Handle update failure"""
        QMessageBox.critical(
            self, "Update Failed",
            f"Failed to install update:\n{error_message}"
        )
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.ssh_manager.disconnect()
        event.accept()
