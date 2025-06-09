"""Terminal session management"""
import os
import re
import threading
import winpty
from PySide6.QtCore import QObject, Signal


class TerminalManager(QObject):
    """Manages terminal sessions"""
    
    output_received = Signal(str)
    connection_closed = Signal()
    
    CSI_RE = re.compile(r'\x1b\[[\?0-9;]*[A-Za-z]')
    
    def __init__(self, host: str, port: int, username: str, password: str):
        """Initialize terminal manager
        
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
        self.pty = None
        self._reader_thread = None
        self._password_sent = False
        
    def start_session(self):
        """Start terminal session"""
        cmd = [
            "ssh", "-tt",
            "-o", "StrictHostKeyChecking=no",
            "-o", "PreferredAuthentications=password",
            "-o", "PubkeyAuthentication=no",
            "-p", str(self.port),
            f"{self.username}@{self.host}"
        ]
        
        self.pty = winpty.PtyProcess.spawn(cmd, env=os.environ)
        
        # Start reader thread
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()
        
    def _read_output(self):
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
                    self.write_input(self.password + "\r")
                    self._password_sent = True
                    
            except OSError:
                break
                
        self.connection_closed.emit()
        
    def write_input(self, text: str):
        """Write input to terminal
        
        Args:
            text: Text to write
        """
        if self.pty:
            self.pty.write(text)
            
    def close_session(self):
        """Close terminal session"""
        if self.pty:
            self.pty.close()
            self.pty = None
