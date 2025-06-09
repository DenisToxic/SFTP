"""
SFTP GUI Manager - Main Entry Point
A modern, feature-rich SFTP client with integrated terminal support
"""
import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.dialogs.connection_dialog import ConnectionDialog
from ui.dialogs.splash_screen import SplashScreen
from core.ssh_manager import SSHManager
from ui.main_window import MainWindow
from utils.theme import apply_dark_theme
from core.version_manager import VersionManager
import json
from pathlib import Path


def migrate_old_config():
    """Migrate configuration from old location to new user data directory"""
    from utils.config import ConfigManager
    
    # Check if old config exists in the application directory
    old_config_path = Path("config.json")
    
    if old_config_path.exists():
        print("🔄 Found old config file, migrating...")
        try:
            # Load old config
            with open(old_config_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
            
            # Create new config manager (will use proper user directory)
            config_manager = ConfigManager()
            
            # Migrate data
            for key, value in old_config.items():
                config_manager.set(key, value)
            
            # Save to new location
            config_manager.save_config()
            
            # Rename old file to prevent future migration
            backup_path = old_config_path.with_suffix('.json.migrated')
            old_config_path.rename(backup_path)
            
            print(f"✅ Config migrated successfully!")
            print(f"📁 New location: {config_manager.config_file}")
            print(f"💾 Old file backed up to: {backup_path}")
            
        except Exception as e:
            print(f"⚠️  Config migration failed: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("SFTP GUI Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SFTP Development Team")
    
    # Migrate old config if needed
    migrate_old_config()
    
    # Apply dark theme
    apply_dark_theme(app)
    
    # Show splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    try:
        # Initialize version manager
        splash.update_status("Initializing version manager...")
        app.processEvents()
        
        version_manager = VersionManager()
        
        # Check for updates on startup
        splash.update_status("Checking for updates...")
        app.processEvents()
        
        def on_update_check_completed(has_update):
            if has_update:
                splash.update_status("Update available!")
            else:
                splash.update_status("Application is up to date")
            app.processEvents()
        
        version_manager.update_check_completed.connect(on_update_check_completed)
        version_manager.check_for_updates(silent=True)
        
        # Show connection dialog
        splash.update_status("Ready to connect...")
        app.processEvents()
        splash.close()
        
        connection_dialog = ConnectionDialog()
        if connection_dialog.exec() != QDialog.Accepted:
            return 0
        
        # Get connection info and establish connection
        host, port, username, password = connection_dialog.get_connection_info()
        
        # Create SSH manager and connect
        ssh_manager = SSHManager()
        ssh_manager.connect(host, port, username, password)
        
        # Create and show main window
        main_window = MainWindow(ssh_manager, version_manager)
        main_window.show()
        
        # Run application
        return app.exec()
        
    except Exception as e:
        if 'splash' in locals():
            splash.close()
        QMessageBox.critical(None, "Error", f"Application failed to start:\n{str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
