# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the project directory
project_dir = Path(os.getcwd())

block_cipher = None

# Define hidden imports - include all dependencies
hidden_imports = [
    'paramiko',
    'winpty',
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'json',
    'tempfile',
    'threading',
    'subprocess',
    'hashlib',
    'time',
    'os',
    'sys',
    'stat',
    'posixpath',
    'shutil',
    're',
    'datetime',
    'dataclasses',
    'typing',
    'pathlib',
]

# Try to include optional dependencies
try:
    import requests
    hidden_imports.append('requests')
    hidden_imports.extend(['urllib3', 'certifi', 'charset_normalizer', 'idna'])
except ImportError:
    pass

try:
    import packaging
    hidden_imports.append('packaging')
    hidden_imports.append('packaging.version')
except ImportError:
    pass

# Data files to include
datas = [
    ('version.json', '.'),
]

# Add README if it exists
readme_path = project_dir / 'README.md'
if readme_path.exists():
    datas.append(('README.md', '.'))

# Add icon if it exists
icon_path = project_dir / 'installer' / 'icon.ico'
if not icon_path.exists():
    # Create a minimal icon file
    icon_path.parent.mkdir(exist_ok=True)
    # Create a simple 16x16 ICO file
    ico_data = bytes([
        0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x10, 0x10, 0x00, 0x00, 0x01, 0x00,
        0x20, 0x00, 0x68, 0x04, 0x00, 0x00, 0x16, 0x00, 0x00, 0x00, 0x28, 0x00,
        0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x01, 0x00,
        0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00
    ] + [0x00, 0x80, 0xFF, 0xFF] * 256)  # Blue pixels
    
    with open(icon_path, 'wb') as f:
        f.write(ico_data)

a = Analysis(
    ['main.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ONEFILE EXECUTABLE - Everything bundled into single .exe
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SFTPGUIManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None
)
