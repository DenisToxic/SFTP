"""Connection dialog implementation"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QPushButton, QCheckBox
)
from PySide6.QtCore import Qt

from utils.config import ConfigManager


class ConnectionDialog(QDialog):
    """Dialog for SSH connection configuration"""
    
    def __init__(self):
        """Initialize connection dialog"""
        super().__init__()
        self.config_manager = ConfigManager()
        self._setup_ui()
        self._load_saved_connections()
        
    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Connect to SSH Server")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QFormLayout(self)
        
        # Connection selector
        self.connection_combo = QComboBox()
        self.connection_combo.addItem("New connection...")
        self.connection_combo.currentTextChanged.connect(self._on_connection_selected)
        layout.addRow("Saved Connections:", self.connection_combo)
        
        # Connection details
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("hostname or IP address")
        
        self.port_edit = QLineEdit("22")
        self.port_edit.setPlaceholderText("22")
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("username")
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("password")
        
        self.save_password_cb = QCheckBox("Save password")
        
        layout.addRow("Host:", self.host_edit)
        layout.addRow("Port:", self.port_edit)
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Password:", self.password_edit)
        layout.addRow("", self.save_password_cb)
        
        # Buttons
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._connect)
        self.connect_btn.setDefault(True)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        layout.addRow(self.connect_btn, self.cancel_btn)
        
    def _load_saved_connections(self):
        """Load saved connections"""
        connections = self.config_manager.get_connections()
        for name in connections.keys():
            self.connection_combo.addItem(name)
            
    def _on_connection_selected(self, name: str):
        """Handle connection selection
        
        Args:
            name: Connection name
        """
        if name == "New connection...":
            self._clear_fields()
            return
            
        connections = self.config_manager.get_connections()
        if name in connections:
            conn = connections[name]
            self.host_edit.setText(conn.get("host", ""))
            self.port_edit.setText(str(conn.get("port", 22)))
            self.username_edit.setText(conn.get("username", ""))
            self.password_edit.setText(conn.get("password", ""))
            self.save_password_cb.setChecked(bool(conn.get("password", "")))
            
    def _clear_fields(self):
        """Clear all input fields"""
        self.host_edit.clear()
        self.port_edit.setText("22")
        self.username_edit.clear()
        self.password_edit.clear()
        self.save_password_cb.setChecked(False)
        
    def _connect(self):
        """Handle connect button click"""
        # Validate input
        if not self.host_edit.text():
            self.host_edit.setFocus()
            return
            
        if not self.username_edit.text():
            self.username_edit.setFocus()
            return
            
        if not self.password_edit.text():
            self.password_edit.setFocus()
            return
            
        # Save connection if requested
        host = self.host_edit.text()
        if host:
            password = self.password_edit.text() if self.save_password_cb.isChecked() else ""
            self.config_manager.save_connection(
                host,  # Use host as name
                host,
                int(self.port_edit.text()),
                self.username_edit.text(),
                password
            )
            
        self.accept()
        
    def get_connection_info(self) -> tuple[str, int, str, str]:
        """Get connection information
        
        Returns:
            Tuple of (host, port, username, password)
        """
        return (
            self.host_edit.text(),
            int(self.port_edit.text()),
            self.username_edit.text(),
            self.password_edit.text()
        )
