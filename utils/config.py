"""Configuration management"""
import json
import os
from typing import Dict, Any, List


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager
        
        Args:
            config_file: Configuration file path
        """
        self.config_file = config_file
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file
        
        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load config: {e}")
        return {}
        
    def save_config(self):
        """Save configuration to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
            
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
