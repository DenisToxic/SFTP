<div align="center">

# 🚀 SFTP GUI Manager

**A modern, feature-rich SFTP client with integrated terminal support**

[![Version](https://img.shields.io/badge/version-1.1.1-blue.svg?style=for-the-badge)](https://github.com/DenisToxic/SFTP/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5.0%2B-brightgreen.svg?style=for-the-badge)](https://wiki.qt.io/Qt_for_Python)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)


*Seamlessly manage remote files with a powerful, intuitive interface*

</div>

---

## ✨ Features

<table>
  <tr>
    <td width="50%">
      <h3>🖥️ Modern Interface</h3>
      <ul>
        <li>Sleek, intuitive file browser with tree-view navigation</li>
        <li>Dark theme support for comfortable extended usage</li>
        <li>Responsive design that adapts to your workspace</li>
        <li>Customizable layout with resizable panels</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🔌 Integrated Terminal</h3>
      <ul>
        <li>Full SSH terminal access alongside file management</li>
        <li>Execute commands directly on your remote server</li>
        <li>Multi-session support with tabbed interface</li>
        <li>Command history and auto-completion</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📂 Advanced File Operations</h3>
      <ul>
        <li>Drag & drop file uploads and downloads</li>
        <li>Edit remote files with your preferred editor</li>
        <li>Auto-sync changes when you save edited files</li>
        <li>Create, delete, rename files and folders</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🛡️ Robust & Secure</h3>
      <ul>
        <li>Automatic retry logic for network operations</li>
        <li>Progress tracking for large file transfers</li>
        <li>Secure password storage with encryption</li>
        <li>Built-in update system to stay current</li>
      </ul>
    </td>
  </tr>
</table>

## 🌟 Highlights

- **Cross-Platform Compatibility**: Works seamlessly on Windows, macOS, and Linux
- **Drag & Drop Support**: Effortlessly transfer files between local and remote systems
- **Real-Time Editing**: Open, edit, and save remote files with automatic synchronization
- **Connection Management**: Save and organize multiple SSH connections
- **Visual Progress Tracking**: See detailed progress for all file operations
- **Automatic Updates**: Stay current with the latest features and security patches

## 🎮 Usage Guide

### Connecting to a Server

<div align="center">
</div>

1. Launch the application
2. Fill in your connection details:
   - **Host**: Your server's IP address or hostname
   - **Port**: SSH port (usually 22)
   - **Username**: Your SSH username
   - **Password**: Your SSH password
3. Optionally save the connection for future use
4. Click "Connect"

### File Management

#### 📤 Uploading Files
- **Drag & Drop**: Drag files from your computer into the file browser
- **Context Menu**: Right-click in the file browser and select "Upload File"
- **Toolbar**: Use the upload button in the toolbar

#### 📥 Downloading Files
- **Double-click**: Double-click a file to download it
- **Context Menu**: Right-click a file and select "Download"
- **Toolbar**: Select a file and use the download button

#### ✏️ Editing Files
- **Double-click**: Double-click a text file to open it in your default editor
- **Auto-sync**: Changes are automatically uploaded when you save the file
- **Editor Selection**: Configure your preferred editor in the settings

### 💻 Terminal Usage

<div align="center">
</div>

The integrated terminal provides full SSH access to your server:
- Execute commands directly on the remote server
- Navigate directories using standard Unix commands
- Run scripts and manage services
- Full terminal emulation with color support

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|:--------:|--------|
| `Ctrl+N` | New Connection |
| `Ctrl+U` | Upload File |
| `Ctrl+D` | Download File |
| `F5` | Refresh Directory |
| `Ctrl+Q` | Quit Application |
| `Delete` | Delete Selected File |
| `Ctrl+A` | Select All (in terminal) |

## 🛠️ Configuration

### Editor Settings

Configure your preferred text editor in the application settings:
- **Windows**: notepad.exe, code (VS Code), notepad++
- **macOS**: TextEdit, code, vim
- **Linux**: gedit, vim, nano, code

### Connection Settings

- **Save Passwords**: Optionally save passwords for quick reconnection
- **Connection Timeout**: Configure connection timeout values
- **Retry Settings**: Adjust retry attempts for failed operations

### Update Settings

- **Auto-check**: Automatically check for updates on startup
- **Auto-install**: Automatically install non-critical updates
- **Pre-releases**: Include beta versions in update checks

## 🔍 Troubleshooting

<details>
<summary><b>Connection Problems</b></summary>

- **"Connection refused"**: Check if SSH service is running on the target server
- **"Authentication failed"**: Verify username and password
- **"Network unreachable"**: Check network connectivity and firewall settings
</details>

<details>
<summary><b>File Transfer Issues</b></summary>

- **"Permission denied"**: Check file permissions on the remote server
- **"File in use"**: Close any applications that might be using the file
- **"Disk full"**: Ensure sufficient disk space on both local and remote systems
</details>

<details>
<summary><b>Editor Problems</b></summary>

- **"Editor not found"**: Verify the editor path in settings
- **"File not uploading"**: Check if the file watcher is running properly
- **"Large file warning"**: Consider using a different editor for very large files
</details>

## 📊 Project Structure

\`\`\`
SFTP-GUI-Manager/
├── 📁 core/                    # Core business logic
│   ├── ssh_manager.py          # SSH connection management
│   ├── file_manager.py         # File operations
│   ├── terminal_manager.py     # Terminal session handling
│   └── version_manager.py      # Update management
├── 📁 ui/                      # User interface
│   ├── 📁 dialogs/            # Dialog windows
│   │   ├── connection_dialog.py
│   │   ├── update_dialog.py
│   │   ├── about_dialog.py
│   │   ├── command_shortcuts_dialog.py
│   │   └── splash_screen.py
│   ├── 📁 widgets/            # UI widgets
│   │   ├── terminal_widget.py
│   │   └── file_browser_widget.py
│   └── main_window.py         # Main application window
├── 📁 utils/                   # Utilities
│   ├── config.py              # Configuration management
│   ├── theme.py               # Application theming
│   └── file_watcher.py        # File change monitoring
├── 📁 build_scripts/          # Build automation
│   ├── build.py               # Unified build script
│   └── build.bat              # Windows build script
├── 📁 installer/              # Installer creation
│   └── installer.py           # Installer script generator
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
\`\`\`

## 🔮 Roadmap

<div align="center">

| Status | Feature | Target Release |
|:------:|---------|:-------------:|
| 🔄 | SSH key authentication | v1.1.1 |
| 🔄 | Bookmark system | v1.1.1 |
| 📅 | File synchronization | v1.2.0 |
| 📅 | Batch operations | v1.2.0 |
| 🔮 | Plugin system | v1.3.0 |
| 🔮 | Tabbed interface | v1.3.0 |
| 🔮 | File comparison tools | v1.4.0 |
| 🔮 | Advanced search | v1.4.0 |

</div>

## 🤝 Contributing

We welcome contributions from the community! Whether it's bug reports, feature requests, or code contributions, please feel free to reach out.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PySide6 Team** - For the excellent Qt bindings
- **Paramiko Team** - For the robust SSH implementation
- **Open Source Community** - For inspiration and contributions

---

<div align="center">

**Made with ❤️ by the SFTP GUI Manager Team**

[![GitHub Stars](https://img.shields.io/github/stars/DenisToxic/SFTP?style=social)](https://github.com/DenisToxic/SFTP)

</div>
