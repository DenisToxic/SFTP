"""File watching utilities"""
import hashlib
import threading
import time
import os
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
        self._last_modified = self._get_modified_time()
        
    def _hash_file(self) -> str:
        """Calculate file hash
        
        Returns:
            MD5 hash of file contents
        """
        try:
            # Use a more robust file reading approach
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    with open(self.filepath, "rb") as f:
                        return hashlib.md5(f.read()).hexdigest()
                except (OSError, PermissionError) as e:
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)  # Wait before retry
                    else:
                        print(f"Warning: Could not read file {self.filepath}: {e}")
                        return ""
        except Exception:
            return ""
            
    def _get_modified_time(self) -> float:
        """Get file modification time
        
        Returns:
            File modification time or 0 if error
        """
        try:
            return os.path.getmtime(self.filepath)
        except Exception:
            return 0
            
    def run(self):
        """Watch file for changes"""
        while self._running:
            try:
                # Check if file still exists
                if not os.path.exists(self.filepath):
                    break
                    
                # Check modification time first (faster than hashing)
                current_modified = self._get_modified_time()
                if current_modified != self._last_modified:
                    # File was modified, now check hash to confirm actual changes
                    current_hash = self._hash_file()
                    if current_hash and current_hash != self._last_hash:
                        self._last_hash = current_hash
                        self._last_modified = current_modified
                        
                        # Call callback with some delay to ensure file is fully written
                        time.sleep(0.5)
                        if self._running:  # Check if still running after delay
                            self.callback(self.filepath)
                    else:
                        self._last_modified = current_modified
                        
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Error in file watcher: {e}")
                time.sleep(2)
                
    def stop(self):
        """Stop watching file"""
        self._running = False
