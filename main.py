"""
SFTP GUI Manager - Main Entry Point
A clean, minimal entry point that delegates to proper modules
"""
import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from ui.dialogs.connection_dialog import ConnectionDialog
from ui.dialogs.splash_screen import SplashScreen
from core.ssh_manager import SSHManager
from ui.main_window import MainWindow
from utils.theme import apply_dark_theme
from core.version_manager import VersionManager


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
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
            return
        
        # Get connection info and establish connection
        host, port, username, password = connection_dialog.get_connection_info()
        
        # Create SSH manager and connect
        ssh_manager = SSHManager()
        ssh_manager.connect(host, port, username, password)
        
        # Create and show main window
        main_window = MainWindow(ssh_manager, version_manager)
        main_window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        if 'splash' in locals():
            splash.close()
        QMessageBox.critical(None, "Error", f"Application failed to start:\n{str(e)}")


if __name__ == "__main__":
    main()
