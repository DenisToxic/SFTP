"""File watching utilities"""
import hashlib
import threading
import time
from typing import Callable


class FileWatcher(threading.Thread):
    """Watches file for changes and triggers callback"""
    
    def __init__(self, filepath: str, callback: Callable[[str], None]):
        """Initialize file watcher
        
        Args:
            filepath: Path to file to watch
            callback: Function to call when file changes
        """
        super().__init__(daemon=True)
        self.filepath = filepath
        self.callback = callback
        self._last_hash = self._hash_file()
        self._running = True
        
    def _hash_file(self) -> str:
        """Calculate file hash
        
        Returns:
            MD5 hash of file contents
        """
        try:
            with open(self.filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
            
    def run(self):
        """Watch file for changes"""
        while self._running:
            time.sleep(2)
            current_hash = self._hash_file()
            if current_hash != self._last_hash:
                self._last_hash = current_hash
                self.callback(self.filepath)
                
    def stop(self):
        """Stop watching file"""
        self._running = False
