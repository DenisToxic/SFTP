"""Command shortcuts management dialog"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QTextEdit, QComboBox, QLabel, QGroupBox,
    QFormLayout, QMessageBox, QInputDialog, QSplitter, QHeaderView,
    QMenu, QAbstractItemView, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction

from utils.config import ConfigManager


class CommandShortcutEditDialog(QDialog):
    """Dialog for editing command shortcuts"""
    
    def __init__(self, shortcut_name: str = "", shortcut_data: dict = None, parent=None):
        """Initialize command shortcut edit dialog
        
        Args:
            shortcut_name: Name of shortcut to edit (empty for new)
            shortcut_data: Existing shortcut data (None for new)
            parent: Parent widget
        """
        super().__init__(parent)
        self.shortcut_name = shortcut_name
        self.shortcut_data = shortcut_data or {}
        self.config_manager = ConfigManager()
        
        self._setup_ui()
        self._populate_data()
        
    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Edit Command Shortcut" if self.shortcut_name else "New Command Shortcut")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_group = QGroupBox("Shortcut Details")
        form_layout = QFormLayout(form_group)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter shortcut name...")
        form_layout.addRow("Name:", self.name_edit)
        
        # Category field
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(["General", "System", "File Operations", "Network", "Development"])
        existing_categories = self.config_manager.get_command_categories()
        for category in existing_categories:
            if category not in ["General", "System", "File Operations", "Network", "Development"]:
                self.category_combo.addItem(category)
        form_layout.addRow("Category:", self.category_combo)
        
        # Description field
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description...")
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(form_group)
        
        # Command group
        command_group = QGroupBox("Command")
        command_layout = QVBoxLayout(command_group)
        
        # Command text area
        self.command_edit = QTextEdit()
        self.command_edit.setPlaceholderText("Enter command(s) to execute...\n\nExamples:\nls -la\ncd /var/log && tail -f syslog\nsudo systemctl status nginx")
        self.command_edit.setFont(QFont("Consolas", 10))
        command_layout.addWidget(self.command_edit)
        
        # Command help
        help_label = QLabel(
            "💡 Tips:\n"
            "• Use && to chain commands\n"
            "• Use ; to run commands sequentially\n"
            "• Use | for pipes\n"
            "• Commands will be executed in the current terminal"
        )
        help_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        help_label.setWordWrap(True)
        command_layout.addWidget(help_label)
        
        layout.addWidget(command_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_shortcut)
        self.save_btn.setDefault(True)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.test_btn = QPushButton("Test Command")
        self.test_btn.clicked.connect(self._test_command)
        
        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def _populate_data(self):
        """Populate form with existing data"""
        if self.shortcut_name:
            self.name_edit.setText(self.shortcut_name)
            self.name_edit.setReadOnly(True)  # Don't allow renaming
            
        if self.shortcut_data:
            self.command_edit.setPlainText(self.shortcut_data.get("command", ""))
            self.description_edit.setText(self.shortcut_data.get("description", ""))
            
            category = self.shortcut_data.get("category", "General")
            index = self.category_combo.findText(category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            else:
                self.category_combo.setCurrentText(category)
                
    def _save_shortcut(self):
        """Save the shortcut"""
        name = self.name_edit.text().strip()
        command = self.command_edit.toPlainText().strip()
        description = self.description_edit.text().strip()
        category = self.category_combo.currentText().strip()
        
        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a shortcut name.")
            self.name_edit.setFocus()
            return
            
        if not command:
            QMessageBox.warning(self, "Validation Error", "Please enter a command.")
            self.command_edit.setFocus()
            return
            
        # Check for duplicate names (only for new shortcuts)
        if not self.shortcut_name:
            existing_shortcuts = self.config_manager.get_command_shortcuts()
            if name in existing_shortcuts:
                QMessageBox.warning(self, "Duplicate Name", f"A shortcut named '{name}' already exists.")
                self.name_edit.setFocus()
                return
                
        # Save shortcut
        self.config_manager.save_command_shortcut(name, command, description, category)
        self.accept()
        
    def _test_command(self):
        """Test the command (show preview)"""
        command = self.command_edit.toPlainText().strip()
        if not command:
            QMessageBox.information(self, "Test Command", "Please enter a command first.")
            return
            
        QMessageBox.information(
            self, "Command Preview",
            f"The following command will be executed in the terminal:\n\n{command}\n\n"
            f"Note: This is just a preview. The actual command will be sent to the active terminal session."
        )


class CommandShortcutsDialog(QDialog):
    """Dialog for managing command shortcuts"""
    
    shortcut_executed = Signal(str)  # command
    
    def __init__(self, parent=None):
        """Initialize command shortcuts dialog
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self._setup_ui()
        self._load_shortcuts()
        
    def _setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("Command Shortcuts Manager")
        self.setModal(False)  # Allow interaction with main window
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("⚡ Command Shortcuts")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search shortcuts...")
        self.search_edit.textChanged.connect(self._filter_shortcuts)
        header_layout.addWidget(self.search_edit)
        
        layout.addLayout(header_layout)
        
        # Main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Shortcuts tree
        self.shortcuts_tree = QTreeWidget()
        self.shortcuts_tree.setHeaderLabels(["Name", "Category", "Description"])
        self.shortcuts_tree.setAlternatingRowColors(True)
        self.shortcuts_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.shortcuts_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.shortcuts_tree.customContextMenuRequested.connect(self._show_context_menu)
        self.shortcuts_tree.itemDoubleClicked.connect(self._execute_shortcut)
        self.shortcuts_tree.currentItemChanged.connect(self._on_selection_changed)
        
        # Set column widths
        header = self.shortcuts_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        splitter.addWidget(self.shortcuts_tree)
        
        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Command preview
        command_group = QGroupBox("Command Preview")
        command_layout = QVBoxLayout(command_group)
        
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setFont(QFont("Consolas", 10))
        self.command_preview.setMaximumHeight(150)
        command_layout.addWidget(self.command_preview)
        
        details_layout.addWidget(command_group)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.execute_btn = QPushButton("⚡ Execute Command")
        self.execute_btn.clicked.connect(self._execute_shortcut)
        self.execute_btn.setEnabled(False)
        actions_layout.addWidget(self.execute_btn)
        
        self.edit_btn = QPushButton("✏️ Edit Shortcut")
        self.edit_btn.clicked.connect(self._edit_shortcut)
        self.edit_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete Shortcut")
        self.delete_btn.clicked.connect(self._delete_shortcut)
        self.delete_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_btn)
        
        actions_layout.addStretch()
        
        details_layout.addWidget(actions_group)
        
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("➕ New Shortcut")
        self.new_btn.clicked.connect(self._new_shortcut)
        
        self.import_btn = QPushButton("📥 Import")
        self.import_btn.clicked.connect(self._import_shortcuts)
        
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self._export_shortcuts)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def _load_shortcuts(self):
        """Load shortcuts into tree"""
        self.shortcuts_tree.clear()
        shortcuts = self.config_manager.get_command_shortcuts()
        
        # Group by category
        categories = {}
        for name, data in shortcuts.items():
            category = data.get("category", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append((name, data))
            
        # Add to tree
        for category, items in sorted(categories.items()):
            category_item = QTreeWidgetItem([f"📁 {category}", "", ""])
            category_item.setData(0, Qt.UserRole, {"type": "category", "name": category})
            self.shortcuts_tree.addTopLevelItem(category_item)
            
            for name, data in sorted(items):
                shortcut_item = QTreeWidgetItem([
                    name,
                    "",
                    data.get("description", "")
                ])
                shortcut_item.setData(0, Qt.UserRole, {
                    "type": "shortcut",
                    "name": name,
                    "data": data
                })
                category_item.addChild(shortcut_item)
                
        # Expand all categories
        self.shortcuts_tree.expandAll()
        
    def _filter_shortcuts(self, text: str):
        """Filter shortcuts based on search text"""
        text = text.lower()
        
        for i in range(self.shortcuts_tree.topLevelItemCount()):
            category_item = self.shortcuts_tree.topLevelItem(i)
            category_visible = False
            
            for j in range(category_item.childCount()):
                shortcut_item = category_item.child(j)
                item_data = shortcut_item.data(0, Qt.UserRole)
                
                if item_data["type"] == "shortcut":
                    name = item_data["name"].lower()
                    description = item_data["data"].get("description", "").lower()
                    command = item_data["data"].get("command", "").lower()
                    
                    visible = (text in name or text in description or text in command)
                    shortcut_item.setHidden(not visible)
                    
                    if visible:
                        category_visible = True
                        
            category_item.setHidden(not category_visible)
            
    def _on_selection_changed(self, current, previous):
        """Handle selection change"""
        if current:
            item_data = current.data(0, Qt.UserRole)
            
            if item_data and item_data["type"] == "shortcut":
                # Show command preview
                command = item_data["data"].get("command", "")
                self.command_preview.setPlainText(command)
                
                # Enable buttons
                self.execute_btn.setEnabled(True)
                self.edit_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
            else:
                # Clear preview and disable buttons
                self.command_preview.clear()
                self.execute_btn.setEnabled(False)
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
        else:
            self.command_preview.clear()
            self.execute_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            
    def _show_context_menu(self, pos):
        """Show context menu"""
        item = self.shortcuts_tree.itemAt(pos)
        if not item:
            return
            
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
            
        menu = QMenu(self)
        
        if item_data["type"] == "shortcut":
            execute_action = QAction("⚡ Execute", self)
            execute_action.triggered.connect(self._execute_shortcut)
            menu.addAction(execute_action)
            
            menu.addSeparator()
            
            edit_action = QAction("✏️ Edit", self)
            edit_action.triggered.connect(self._edit_shortcut)
            menu.addAction(edit_action)
            
            delete_action = QAction("🗑️ Delete", self)
            delete_action.triggered.connect(self._delete_shortcut)
            menu.addAction(delete_action)
            
        elif item_data["type"] == "category":
            new_action = QAction("➕ New Shortcut in Category", self)
            new_action.triggered.connect(lambda: self._new_shortcut(item_data["name"]))
            menu.addAction(new_action)
            
        menu.exec(self.shortcuts_tree.viewport().mapToGlobal(pos))
        
    def _execute_shortcut(self):
        """Execute selected shortcut"""
        current_item = self.shortcuts_tree.currentItem()
        if not current_item:
            return
            
        item_data = current_item.data(0, Qt.UserRole)
        if item_data and item_data["type"] == "shortcut":
            command = item_data["data"].get("command", "")
            if command:
                self.shortcut_executed.emit(command)
                
    def _new_shortcut(self, category: str = "General"):
        """Create new shortcut"""
        dialog = CommandShortcutEditDialog(parent=self)
        if category != "General":
            dialog.category_combo.setCurrentText(category)
            
        if dialog.exec() == QDialog.Accepted:
            self._load_shortcuts()
            
    def _edit_shortcut(self):
        """Edit selected shortcut"""
        current_item = self.shortcuts_tree.currentItem()
        if not current_item:
            return
            
        item_data = current_item.data(0, Qt.UserRole)
        if item_data and item_data["type"] == "shortcut":
            dialog = CommandShortcutEditDialog(
                item_data["name"],
                item_data["data"],
                parent=self
            )
            
            if dialog.exec() == QDialog.Accepted:
                self._load_shortcuts()
                
    def _delete_shortcut(self):
        """Delete selected shortcut"""
        current_item = self.shortcuts_tree.currentItem()
        if not current_item:
            return
            
        item_data = current_item.data(0, Qt.UserRole)
        if item_data and item_data["type"] == "shortcut":
            name = item_data["name"]
            
            reply = QMessageBox.question(
                self, "Delete Shortcut",
                f"Are you sure you want to delete the shortcut '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.config_manager.delete_command_shortcut(name)
                self._load_shortcuts()
                
    def _import_shortcuts(self):
        """Import shortcuts from file"""
        from PySide6.QtWidgets import QFileDialog
        import json
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Command Shortcuts",
            "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported_shortcuts = json.load(f)
                    
                # Validate format
                if not isinstance(imported_shortcuts, dict):
                    raise ValueError("Invalid file format")
                    
                # Import shortcuts
                existing_shortcuts = self.config_manager.get_command_shortcuts()
                conflicts = []
                
                for name, data in imported_shortcuts.items():
                    if name in existing_shortcuts:
                        conflicts.append(name)
                        
                # Handle conflicts
                if conflicts:
                    reply = QMessageBox.question(
                        self, "Import Conflicts",
                        f"The following shortcuts already exist:\n{', '.join(conflicts)}\n\n"
                        f"Do you want to overwrite them?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply != QMessageBox.Yes:
                        return
                        
                # Import all shortcuts
                for name, data in imported_shortcuts.items():
                    self.config_manager.save_command_shortcut(
                        name,
                        data.get("command", ""),
                        data.get("description", ""),
                        data.get("category", "General")
                    )
                    
                self._load_shortcuts()
                QMessageBox.information(
                    self, "Import Successful",
                    f"Successfully imported {len(imported_shortcuts)} shortcuts."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error",
                    f"Failed to import shortcuts:\n{str(e)}"
                )
                
    def _export_shortcuts(self):
        """Export shortcuts to file"""
        from PySide6.QtWidgets import QFileDialog
        import json
        
        shortcuts = self.config_manager.get_command_shortcuts()
        if not shortcuts:
            QMessageBox.information(self, "No Shortcuts", "No shortcuts to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Command Shortcuts",
            "command_shortcuts.json", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(shortcuts, f, indent=2)
                    
                QMessageBox.information(
                    self, "Export Successful",
                    f"Successfully exported {len(shortcuts)} shortcuts to:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export shortcuts:\n{str(e)}"
                )
