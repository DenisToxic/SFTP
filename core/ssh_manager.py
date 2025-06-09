"""SSH Connection and SFTP Management"""
import paramiko
import time
from typing import Optional, Callable, Any
from PySide6.QtCore import QObject, Signal


class SSHManager(QObject):
    """Manages SSH connections and SFTP operations"""
    
    connection_lost = Signal()
    operation_progress = Signal(int, int)  # transferred, total
    
    def __init__(self):
        """Initialize SSH manager"""
        super().__init__()
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.sftp_client: Optional[paramiko.SFTPClient] = None
        self.host = ""
        self.port = 22
        self.username = ""
        self.password = ""
        
    def connect(self, host: str, port: int, username: str, password: str, timeout: int = 30):
        """Establish SSH connection and create SFTP client
        
        Args:
            host: SSH server hostname
            port: SSH server port
            username: SSH username
            password: SSH password
            timeout: Connection timeout in seconds
            
        Raises:
            paramiko.SSHException: If connection fails
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout
        )
        
        self.sftp_client = self.ssh_client.open_sftp()
        
    def disconnect(self):
        """Close SSH and SFTP connections"""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
            
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
            
    def is_connected(self) -> bool:
        """Check if connection is active
        
        Returns:
            True if connected, False otherwise
        """
        return self.ssh_client is not None and self.sftp_client is not None
        
    def safe_operation(self, operation: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
        """Execute SFTP operation with retry logic
        
        Args:
            operation: SFTP operation to execute
            max_retries: Maximum number of retries
            *args: Arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (OSError, IOError, paramiko.SSHException) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"Operation failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(1)
                    
        if last_exception:
            raise last_exception
            
    def get_sftp(self) -> paramiko.SFTPClient:
        """Get SFTP client instance
        
        Returns:
            SFTP client instance
            
        Raises:
            ConnectionError: If SFTP client is not connected
        """
        if not self.sftp_client:
            raise ConnectionError("SFTP client not connected")
        return self.sftp_client
        
    def execute_command(self, command: str) -> tuple[str, str, int]:
        """Execute SSH command and return stdout, stderr, exit_code
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
            
        Raises:
            ConnectionError: If SSH client is not connected
        """
        if not self.ssh_client:
            raise ConnectionError("SSH client not connected")
            
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        
        return (
            stdout.read().decode('utf-8'),
            stderr.read().decode('utf-8'),
            exit_code
        )
