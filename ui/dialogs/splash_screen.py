"""Splash screen for application startup"""
from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QPainter


class SplashScreen(QSplashScreen):
    """Splash screen shown during application startup"""
    
    def __init__(self):
        """Initialize splash screen"""
        # Create a simple colored pixmap
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.darkBlue)
        
        # Draw text on pixmap
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 24, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "SFTP GUI Manager")
        painter.end()
        
        # Initialize with the pixmap
        super().__init__(pixmap)
        
        # Set window properties
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        
        # Show initial message
        self.showMessage("Starting application...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        
    def update_status(self, message: str):
        """Update status message"""
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        
    def close_after_delay(self, delay_ms: int = 2000):
        """Close splash screen after delay"""
        QTimer.singleShot(delay_ms, self.close)
