"""Update notification and management dialog"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QCheckBox, QGroupBox, QFormLayout, QSpinBox,
    QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.version_manager import VersionManager, VersionInfo


class UpdateDialog(QDialog):
    """Dialog for update notifications and settings"""
    
    def __init__(self, version_info: VersionInfo = None, parent=None):
        """Initialize update dialog
        
        Args:
            version_info: Version information (optional)
            parent: Parent widget
        """
        super().__init__(parent)
        self.version_info = version_info
        self.version_manager = VersionManager()
        self._setup_ui()
        self._setup_connections()
        
        if version_info:
            self._populate_update_info()
            
    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Software Update")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        if self.version_info:
            # Update available section
            self._create_update_section(layout)
        else:
            # Settings only section
            self._create_settings_section(layout)
            
        # Buttons
        self._create_buttons(layout)
        
    def _create_update_section(self, layout):
        """Create update information section
        
        Args:
            layout: Parent layout
        """
        # Header
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel("🔄")
        icon_label.setFont(QFont("Arial", 24))
        header_layout.addWidget(icon_label)
        
        # Title and version
        title_layout = QVBoxLayout()
        title_label = QLabel("Update Available")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        version_label = QLabel(f"Version {self.version_info.version}")
        version_label.setFont(QFont("Arial", 12))
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Current vs new version
        version_info_layout = QHBoxLayout()
        current_label = QLabel(f"Current: {self.version_manager.get_current_version()}")
        new_label = QLabel(f"New: {self.version_info.version}")
        
        if self.version_info.is_critical:
            critical_label = QLabel("⚠️ Critical Update")
            critical_label.setStyleSheet("color: red; font-weight: bold;")
            version_info_layout.addWidget(critical_label)
            
        version_info_layout.addWidget(current_label)
        version_info_layout.addWidget(new_label)
        version_info_layout.addStretch()
        
        layout.addLayout(version_info_layout)
        
        # Changelog
        changelog_group = QGroupBox("What's New")
        changelog_layout = QVBoxLayout(changelog_group)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setMaximumHeight(150)
        self.changelog_text.setReadOnly(True)
        changelog_layout.addWidget(self.changelog_text)
        
        layout.addWidget(changelog_group)
        
        # Settings section
        self._create_settings_section(layout)
        
    def _create_settings_section(self, layout):
        """Create update settings section
        
        Args:
            layout: Parent layout
        """
        settings_group = QGroupBox("Update Settings")
        settings_layout = QFormLayout(settings_group)
        
        # Auto-check updates
        self.auto_check_cb = QCheckBox("Automatically check for updates")
        self.auto_check_cb.setChecked(self.version_manager.auto_check_enabled)
        settings_layout.addRow(self.auto_check_cb)
        
        # Auto-install updates
        self.auto_install_cb = QCheckBox("Automatically install non-critical updates")
        self.auto_install_cb.setChecked(self.version_manager.auto_install_enabled)
        settings_layout.addRow(self.auto_install_cb)
        
        # Include prereleases
        self.prereleases_cb = QCheckBox("Include pre-release versions")
        self.prereleases_cb.setChecked(self.version_manager.include_prereleases)
        settings_layout.addRow(self.prereleases_cb)
        
        # Check interval
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 168)  # 1 hour to 1 week
        self.check_interval_spin.setValue(24)  # Default 24 hours
        self.check_interval_spin.setSuffix(" hours")
        settings_layout.addRow("Check interval:", self.check_interval_spin)
        
        layout.addWidget(settings_group)
        
    def _create_buttons(self, layout):
        """Create dialog buttons
        
        Args:
            layout: Parent layout
        """
        button_layout = QHBoxLayout()
        
        if self.version_info:
            # Update buttons
            self.install_btn = QPushButton("Install Update")
            self.install_btn.setDefault(True)
            
            self.skip_btn = QPushButton("Skip This Version")
            self.later_btn = QPushButton("Remind Me Later")
            
            if self.version_info.is_critical:
                self.install_btn.setText("Install Critical Update")
                self.install_btn.setStyleSheet("background-color: #d32f2f; color: white;")
                
            button_layout.addWidget(self.install_btn)
            button_layout.addWidget(self.skip_btn)
            button_layout.addWidget(self.later_btn)
        else:
            # Settings only buttons
            self.check_now_btn = QPushButton("Check for Updates Now")
            self.ok_btn = QPushButton("OK")
            self.ok_btn.setDefault(True)
            
            button_layout.addWidget(self.check_now_btn)
            button_layout.addStretch()
            button_layout.addWidget(self.ok_btn)
            
        layout.addLayout(button_layout)
        
    def _setup_connections(self):
        """Setup signal connections"""
        if self.version_info:
            self.install_btn.clicked.connect(self._install_update)
            self.skip_btn.clicked.connect(self._skip_version)
            self.later_btn.clicked.connect(self.reject)
        else:
            self.check_now_btn.clicked.connect(self._check_for_updates)
            self.ok_btn.clicked.connect(self._save_settings)
            
        # Settings connections
        self.auto_check_cb.toggled.connect(self.version_manager.set_auto_check_enabled)
        self.auto_install_cb.toggled.connect(self.version_manager.set_auto_install_enabled)
        self.prereleases_cb.toggled.connect(self.version_manager.set_include_prereleases)
        
    def _populate_update_info(self):
        """Populate update information"""
        if self.version_info and hasattr(self, 'changelog_text'):
            self.changelog_text.setPlainText(self.version_info.changelog)
            
    def _install_update(self):
        """Install the update"""
        self.accept()
        self.version_manager.download_and_install_update(self.version_info)
        
    def _skip_version(self):
        """Skip this version"""
        # Save skipped version to config
        self.version_manager.config_manager.set(
            "skipped_version", 
            self.version_info.version
        )
        self.version_manager.config_manager.save_config()
        self.reject()
        
    def _check_for_updates(self):
        """Check for updates now"""
        self.check_now_btn.setEnabled(False)
        self.check_now_btn.setText("Checking...")
        
        def on_check_completed(has_update):
            self.check_now_btn.setEnabled(True)
            self.check_now_btn.setText("Check for Updates Now")
            
            if not has_update:
                QMessageBox.information(
                    self, "No Updates",
                    "You are running the latest version."
                )
                
        self.version_manager.update_check_completed.connect(on_check_completed)
        self.version_manager.check_for_updates(silent=False)
        
    def _save_settings(self):
        """Save settings and close dialog"""
        # Settings are saved automatically via signal connections
        self.accept()


class UpdateProgressDialog(QDialog):
    """Dialog showing update progress"""
    
    def __init__(self, parent=None):
        """Initialize update progress dialog
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Installing Update")
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Preparing update...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Details label
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)
        
    def set_status(self, status: str):
        """Set status text
        
        Args:
            status: Status message
        """
        self.status_label.setText(status)
        
    def set_progress(self, value: int, maximum: int = 100):
        """Set progress value
        
        Args:
            value: Progress value
            maximum: Maximum value
        """
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        
    def set_details(self, details: str):
        """Set details text
        
        Args:
            details: Details message
        """
        self.details_label.setText(details)
