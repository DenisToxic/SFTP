"""Configuration management"""
import json
import os
from typing import Dict, Any, List
from pathlib import Path


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = None):
        """Initialize configuration manager
        
        Args:
            config_file: Configuration file path (optional)
        """
        if config_file is None:
            # Use proper user data directory
            self.config_dir = self._get_user_data_dir()
            self.config_file = self.config_dir / "config.json"
        else:
            self.config_file = Path(config_file)
            self.config_dir = self.config_file.parent
            
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._config = self._load_config()
        
    def _get_user_data_dir(self) -> Path:
        """Get the appropriate user data directory for the platform
        
        Returns:
            Path to user data directory
        """
        app_name = "SFTP GUI Manager"
        
        if os.name == 'nt':  # Windows
            # Use %APPDATA%\SFTP GUI Manager
            appdata = os.environ.get('APPDATA', '')
            if appdata:
                return Path(appdata) / app_name
            else:
                # Fallback to user home
                return Path.home() / f".{app_name.lower().replace(' ', '_')}"
        else:
            # Unix-like systems (Linux, macOS)
            # Use ~/.config/sftp-gui-manager or ~/.sftp-gui-manager
            config_home = os.environ.get('XDG_CONFIG_HOME', '')
            if config_home:
                return Path(config_home) / "sftp-gui-manager"
            else:
                return Path.home() / ".config" / "sftp-gui-manager"
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file
        
        Returns:
            Configuration dictionary
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ Loaded config from: {self.config_file}")
                return config
            except Exception as e:
                print(f"⚠️  Failed to load config from {self.config_file}: {e}")
                return {}
        else:
            print(f"📝 Config file not found, will create: {self.config_file}")
            return {}
        
    def save_config(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved config to: {self.config_file}")
        except Exception as e:
            print(f"❌ Failed to save config to {self.config_file}: {e}")
            # Try to save to a backup location
            try:
                backup_path = Path.home() / "sftp_config_backup.json"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                print(f"💾 Saved backup config to: {backup_path}")
            except Exception as backup_error:
                print(f"❌ Failed to save backup config: {backup_error}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        
    def get_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get saved connections
        
        Returns:
            Dictionary of saved connections
        """
        return self.get("connections", {})
        
    def save_connection(self, name: str, host: str, port: int, username: str, password: str = ""):
        """Save connection details
        
        Args:
            name: Connection name
            host: SSH server hostname
            port: SSH server port
            username: SSH username
            password: SSH password
        """
        connections = self.get_connections()
        connections[name] = {
            "host": host,
            "port": port,
            "username": username,
            "password": password
        }
        self.set("connections", connections)
        self.save_config()
        print(f"💾 Saved connection: {name}")

    def get_command_shortcuts(self) -> Dict[str, Dict[str, str]]:
        """Get saved command shortcuts
        
        Returns:
            Dictionary of command shortcuts
        """
        return self.get("command_shortcuts", {})
        
    def save_command_shortcut(self, name: str, command: str, description: str = "", category: str = "General"):
        """Save command shortcut
        
        Args:
            name: Shortcut name
            command: Command to execute
            description: Optional description
            category: Command category
        """
        shortcuts = self.get_command_shortcuts()
        shortcuts[name] = {
            "command": command,
            "description": description,
            "category": category
        }
        self.set("command_shortcuts", shortcuts)
        self.save_config()
        
    def delete_command_shortcut(self, name: str):
        """Delete command shortcut
        
        Args:
            name: Shortcut name to delete
        """
        shortcuts = self.get_command_shortcuts()
        if name in shortcuts:
            del shortcuts[name]
            self.set("command_shortcuts", shortcuts)
            self.save_config()
        
    def get_command_categories(self) -> List[str]:
        """Get list of command categories
        
        Returns:
            List of category names
        """
        shortcuts = self.get_command_shortcuts()
        categories = set()
        for shortcut in shortcuts.values():
            categories.add(shortcut.get("category", "General"))
        return sorted(list(categories))
        
    def get_config_info(self) -> Dict[str, str]:
        """Get configuration file information for debugging
        
        Returns:
            Dictionary with config file info
        """
        return {
            "config_file": str(self.config_file),
            "config_dir": str(self.config_dir),
            "config_exists": str(self.config_file.exists()),
            "config_writable": str(os.access(self.config_dir, os.W_OK)),
            "connections_count": str(len(self.get_connections())),
            "shortcuts_count": str(len(self.get_command_shortcuts()))
        }
