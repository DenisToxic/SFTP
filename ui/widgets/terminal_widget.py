"""Terminal widget implementation"""
import os
import re
import threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PySide6.QtGui import QFont, QTextCursor, QAction, QKeySequence
from PySide6.QtCore import Qt, Signal
import winpty


class TerminalWidget(QWidget):
    """Terminal widget for SSH sessions"""
    
    output_received = Signal(str)
    CSI_RE = re.compile(r'\x1b\[[\?0-9;]*[A-Za-z]')
    
    def __init__(self, host: str, port: int, username: str, password: str):
        """Initialize terminal widget
        
        Args:
            host: SSH server hostname
            port: SSH server port
            username: SSH username
            password: SSH password
        """
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._password_sent = False
        self.pty = None
        
        self._setup_ui()
        self._start_terminal()
        
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create console
        self.console = QPlainTextEdit()
        self.console.setReadOnly(False)
        self.console.setFont(QFont("Consolas", 11))
        self.console.installEventFilter(self)
        
        layout.addWidget(self.console)
        
        # Setup shortcuts
        self._setup_shortcuts()
        
        # Connect signals
        self.output_received.connect(self._append_output)
        
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        try:
            select_all_action = QAction("Select All", self)
            select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
            select_all_action.triggered.connect(self.console.selectAll)
            self.addAction(select_all_action)
        except Exception as e:
            print(f"Warning: Could not setup shortcuts: {e}")
            
    def _start_terminal(self):
        """Start terminal session"""
        # Spawn SSH process
        cmd = [
            "ssh", "-tt",
            "-o", "StrictHostKeyChecking=no",
            "-o", "PreferredAuthentications=password",
            "-o", "PubkeyAuthentication=no",
            "-o", "PubkeyAuthentication=no",
            "-p", str(self.port),
            f"{self.username}@{self.host}"
        ]
        
        self.pty = winpty.PtyProcess.spawn(cmd, env=os.environ)
        
        # Start reader thread
        threading.Thread(target=self._reader, daemon=True).start()
        
    def _reader(self):
        """Read output from terminal"""
        while True:
            try:
                data = self.pty.read(1024)
                if not data:
                    break
                    
                text = data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else data
                clean_text = self.CSI_RE.sub("", text)
                self.output_received.emit(clean_text)
                
                # Auto-send password when prompted
                if not self._password_sent and re.search(r"[Pp]assword:", clean_text):
                    self.pty.write(self.password + "\r")
                    self._password_sent = True
                    
            except OSError:
                break
                
    def _append_output(self, text: str):
        """Append text to console"""
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()
        
    def eventFilter(self, source, event):
        """Handle key events"""
        if source is self.console and event.type() == event.Type.KeyPress:
            text = event.text()
            if text and self.pty:
                self.pty.write(text)
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.pty:
                self.pty.write("\r")
            return True
        return super().eventFilter(source, event)
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.matches(QKeySequence.StandardKey.SelectAll):
            self.console.selectAll()
            return
        super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """Handle close event"""
        if self.pty:
            self.pty.close()
            self.pty = None
        event.accept()

    def write_input(self, text: str):
        """Write input to terminal
        
        Args:
            text: Text to write to terminal
        """
        if self.pty:
            self.pty.write(text)
