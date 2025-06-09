"""File operations and management"""
import os
import stat
import posixpath
import tempfile
from typing import List, Optional, Callable
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from core.ssh_manager import SSHManager


@dataclass
class RemoteFileInfo:
    """Information about a remote file"""
    filename: str
    size: int
    is_directory: bool
    permissions: int
    modified_time: float
    
    @property
    def size_formatted(self) -> str:
        """Human readable file size"""
        if self.is_directory:
            return ""
        
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class FileManager(QObject):
    """Manages file operations on remote server"""
    
    file_uploaded = Signal(str)  # filename
    file_downloaded = Signal(str)  # filename
    directory_changed = Signal(str)  # new_path
    operation_progress = Signal(int, int)  # transferred, total
    
    def __init__(self, ssh_manager: SSHManager):
        """Initialize file manager
        
        Args:
            ssh_manager: SSH manager instance
        """
        super().__init__()
        self.ssh_manager = ssh_manager
        self.current_path = "."
        self.path_history = []
        
    def list_directory(self, path: str = None) -> List[RemoteFileInfo]:
        """List files in remote directory
        
        Args:
            path: Remote directory path (optional)
            
        Returns:
            List of RemoteFileInfo objects
            
        Raises:
            Exception: If directory listing fails
        """
        if path is None:
            path = self.current_path
            
        sftp = self.ssh_manager.get_sftp()
        
        def _list_operation():
            sftp.chdir(path)
            self.current_path = sftp.getcwd()
            files = []
            
            for file_attr in sftp.listdir_attr():
                files.append(RemoteFileInfo(
                    filename=file_attr.filename,
                    size=file_attr.st_size or 0,
                    is_directory=stat.S_ISDIR(file_attr.st_mode),
                    permissions=file_attr.st_mode,
                    modified_time=file_attr.st_mtime or 0
                ))
                
            return sorted(files, key=lambda f: (not f.is_directory, f.filename.lower()))
            
        files = self.ssh_manager.safe_operation(_list_operation)
        self.directory_changed.emit(self.current_path)
        return files
        
    def change_directory(self, path: str):
        """Change current directory
        
        Args:
            path: Remote directory path
        """
        self.path_history.append(self.current_path)
        self.list_directory(path)
        
    def go_back(self) -> bool:
        """Go back to previous directory
        
        Returns:
            True if successful, False otherwise
        """
        if self.path_history:
            previous_path = self.path_history.pop()
            self.list_directory(previous_path)
            return True
        return False
        
    def go_up(self):
        """Go to parent directory"""
        parent_path = posixpath.dirname(self.current_path)
        if parent_path != self.current_path:
            self.change_directory(parent_path)
            
    def upload_file(self, local_path: str, remote_filename: str = None, 
                   progress_callback: Callable[[int, int], bool] = None):
        """Upload file to remote server
        
        Args:
            local_path: Local file path
            remote_filename: Remote filename (optional)
            progress_callback: Progress callback function (optional)
        """
        if remote_filename is None:
            remote_filename = os.path.basename(local_path)
            
        remote_path = posixpath.join(self.current_path, remote_filename)
        sftp = self.ssh_manager.get_sftp()
        
        def _upload_operation():
            if progress_callback:
                sftp.put(local_path, remote_path, callback=progress_callback)
            else:
                sftp.put(local_path, remote_path)
                
        self.ssh_manager.safe_operation(_upload_operation)
        self.file_uploaded.emit(remote_filename)
        
    def download_file(self, remote_filename: str, local_path: str,
                     progress_callback: Callable[[int, int], bool] = None):
        """Download file from remote server
        
        Args:
            remote_filename: Remote filename
            local_path: Local file path
            progress_callback: Progress callback function (optional)
        """
        remote_path = posixpath.join(self.current_path, remote_filename)
        sftp = self.ssh_manager.get_sftp()
        
        def _download_operation():
            if progress_callback:
                sftp.get(remote_path, local_path, callback=progress_callback)
            else:
                sftp.get(remote_path, local_path)
                
        self.ssh_manager.safe_operation(_download_operation)
        self.file_downloaded.emit(remote_filename)
        
    def delete_file(self, filename: str):
        """Delete file or directory
        
        Args:
            filename: Remote filename
        """
        remote_path = posixpath.join(self.current_path, filename)
        sftp = self.ssh_manager.get_sftp()
        
        def _delete_operation():
            file_stat = sftp.stat(remote_path)
            if stat.S_ISDIR(file_stat.st_mode):
                sftp.rmdir(remote_path)
            else:
                sftp.remove(remote_path)
                
        self.ssh_manager.safe_operation(_delete_operation)
        
    def rename_file(self, old_name: str, new_name: str):
        """Rename file or directory
        
        Args:
            old_name: Old filename
            new_name: New filename
        """
        old_path = posixpath.join(self.current_path, old_name)
        new_path = posixpath.join(self.current_path, new_name)
        sftp = self.ssh_manager.get_sftp()
        
        self.ssh_manager.safe_operation(sftp.rename, old_path, new_path)
        
    def create_file(self, filename: str):
        """Create empty file
        
        Args:
            filename: Remote filename
        """
        remote_path = posixpath.join(self.current_path, filename)
        sftp = self.ssh_manager.get_sftp()
        
        def _create_operation():
            with sftp.open(remote_path, 'w') as f:
                pass  # Create empty file
                
        self.ssh_manager.safe_operation(_create_operation)
        
    def create_directory(self, dirname: str):
        """Create directory
        
        Args:
            dirname: Directory name
        """
        remote_path = posixpath.join(self.current_path, dirname)
        sftp = self.ssh_manager.get_sftp()
        
        self.ssh_manager.safe_operation(sftp.mkdir, remote_path)
        
    def get_file_for_editing(self, filename: str) -> str:
        """Download file to temporary location for editing
        
        Args:
            filename: Remote filename
            
        Returns:
            Local temporary file path
        """
        remote_path = posixpath.join(self.current_path, filename)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f"_{filename}",
            prefix="sftp_edit_"
        )
        temp_path = temp_file.name
        temp_file.close()
        
        # Download file
        self.download_file(filename, temp_path)
        return temp_path
        
    def upload_edited_file(self, temp_path: str, remote_filename: str):
        """Upload edited file back to server
        
        Args:
            temp_path: Local temporary file path
            remote_filename: Remote filename
        """
        self.upload_file(temp_path, remote_filename)
