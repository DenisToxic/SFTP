"""
Test configuration system
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import ConfigManager


def test_config_system():
    """Test the configuration system"""
    print("🔧 Configuration System Test")
    print("=" * 40)
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Show config info
    config_info = config_manager.get_config_info()
    print("📋 Configuration Information:")
    for key, value in config_info.items():
        print(f"  {key}: {value}")
    
    print()
    
    # Test saving a connection
    print("💾 Testing connection save...")
    try:
        config_manager.save_connection(
            "test-server",
            "192.168.1.100", 
            22, 
            "testuser", 
            "testpass"
        )
        print("✅ Connection save successful")
    except Exception as e:
        print(f"❌ Connection save failed: {e}")
    
    # Test loading connections
    print("📖 Testing connection load...")
    try:
        connections = config_manager.get_connections()
        print(f"✅ Loaded {len(connections)} connections")
        for name in connections.keys():
            print(f"  - {name}")
    except Exception as e:
        print(f"❌ Connection load failed: {e}")
    
    # Test saving a shortcut
    print("⚡ Testing shortcut save...")
    try:
        config_manager.save_command_shortcut(
            "list-files",
            "ls -la",
            "List all files with details",
            "File Operations"
        )
        print("✅ Shortcut save successful")
    except Exception as e:
        print(f"❌ Shortcut save failed: {e}")
    
    # Test loading shortcuts
    print("📖 Testing shortcut load...")
    try:
        shortcuts = config_manager.get_command_shortcuts()
        print(f"✅ Loaded {len(shortcuts)} shortcuts")
        for name in shortcuts.keys():
            print(f"  - {name}")
    except Exception as e:
        print(f"❌ Shortcut load failed: {e}")
    
    print()
    print("🎯 Test Summary:")
    print(f"  Config directory: {config_manager.config_dir}")
    print(f"  Config file: {config_manager.config_file}")
    print(f"  Directory writable: {os.access(config_manager.config_dir, os.W_OK)}")
    print(f"  File exists: {config_manager.config_file.exists()}")
    
    if config_manager.config_file.exists():
        stat = config_manager.config_file.stat()
        print(f"  File size: {stat.st_size} bytes")
        print(f"  File writable: {os.access(config_manager.config_file, os.W_OK)}")


if __name__ == "__main__":
    test_config_system()
