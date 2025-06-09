"""About dialog with version information"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.version_manager import VersionManager


class AboutDialog(QDialog):
    """About dialog showing application information"""
    
    def __init__(self, parent=None):
        """Initialize about dialog
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.version_manager = VersionManager()
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("About SFTP GUI Manager")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # App icon
        icon_label = QLabel("📁")
        icon_label.setFont(QFont("Arial", 48))
        header_layout.addWidget(icon_label)
        
        # Title and version
        title_layout = QVBoxLayout()
        title_label = QLabel("SFTP GUI Manager")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        
        version_label = QLabel(f"Version {self.version_manager.get_current_version()}")
        version_label.setFont(QFont("Arial", 12))
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Description
        description = QLabel(
            "A modern, feature-rich SFTP client with integrated terminal support.\n"
            "Built with Python and PySide6 for cross-platform compatibility."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Version details
        version_group = QGroupBox("Version Information")
        version_layout = QGridLayout(version_group)
        
        version_info = self.version_manager.get_version_info()
        
        row = 0
        for key, value in version_info.items():
            label = QLabel(f"{key.replace('_', ' ').title()}:")
            label.setAlignment(Qt.AlignRight)
            value_label = QLabel(str(value))
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            version_layout.addWidget(label, row, 0)
            version_layout.addWidget(value_label, row, 1)
            row += 1
            
        layout.addWidget(version_group)
        
        # Config information
        config_group = QGroupBox("Configuration Information")
        config_layout = QGridLayout(config_group)
        
        from utils.config import ConfigManager
        config_manager = ConfigManager()
        config_info = config_manager.get_config_info()
        
        row = 0
        for key, value in config_info.items():
            label = QLabel(f"{key.replace('_', ' ').title()}:")
            label.setAlignment(Qt.AlignRight)
            value_label = QLabel(str(value))
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            # Color code some values
            if key == "config_writable" and value == "True":
                value_label.setStyleSheet("color: green;")
            elif key == "config_writable" and value == "False":
                value_label.setStyleSheet("color: red; font-weight: bold;")
            elif key == "config_exists" and value == "True":
                value_label.setStyleSheet("color: green;")
            
            config_layout.addWidget(label, row, 0)
            config_layout.addWidget(value_label, row, 1)
            row += 1
            
        layout.addWidget(config_group)
        
        # Credits
        credits_group = QGroupBox("Credits")
        credits_layout = QVBoxLayout(credits_group)
        
        credits_text = QTextEdit()
        credits_text.setMaximumHeight(100)
        credits_text.setReadOnly(True)
        credits_text.setPlainText(
            "Developed by: Your Name\n"
            "Built with: Python, PySide6, Paramiko\n"
            "Icons: Various open source icon sets\n"
            "Special thanks to the open source community"
        )
        credits_layout.addWidget(credits_text)
        
        layout.addWidget(credits_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.check_updates_btn = QPushButton("Check for Updates")
        self.debug_btn = QPushButton("Update Debug")
        self.debug_btn.clicked.connect(self._show_debug_info)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setDefault(True)
        
        button_layout.addWidget(self.check_updates_btn)
        button_layout.addWidget(self.debug_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.check_updates_btn.clicked.connect(self._check_for_updates)
        self.ok_btn.clicked.connect(self.accept)
        
    def _check_for_updates(self):
        """Check for updates"""
        from ui.dialogs.update_dialog import UpdateDialog
        
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setText("Checking...")
        
        def on_update_available(version_info):
            self.check_updates_btn.setEnabled(True)
            self.check_updates_btn.setText("Check for Updates")
            
            update_dialog = UpdateDialog(version_info, self)
            update_dialog.exec()
            
        def on_check_completed(has_update):
            self.check_updates_btn.setEnabled(True)
            self.check_updates_btn.setText("Check for Updates")
            
            if not has_update:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, "No Updates",
                    "You are running the latest version."
                )
                
        self.version_manager.update_available.connect(on_update_available)
        self.version_manager.update_check_completed.connect(on_check_completed)
        self.version_manager.check_for_updates(silent=False)

    def _show_debug_info(self):
        """Show update debug information"""
        self.version_manager.show_update_debug_info()
