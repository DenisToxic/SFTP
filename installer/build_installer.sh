#!/bin/bash

echo "Building SFTP GUI Manager Installer"
echo "===================================="

# Get version from argument or use default
VERSION=${1:-"1.1.0"}
echo "Version: $VERSION"

# Check if PyInstaller dist folder exists
if [ ! -f "../dist/main.exe" ]; then
    echo "Error: main.exe not found in dist folder"
    echo "Please run PyInstaller first:"
    echo "  pyinstaller main.spec"
    exit 1
fi

# Create installer
echo ""
echo "Creating installer..."
python3 create_installer.py "$VERSION"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installer build completed successfully!"
    echo ""
    echo "Output files:"
    ls -la output/*.exe 2>/dev/null || echo "No .exe files found (this is normal on non-Windows systems)"
    echo ""
else
    echo ""
    echo "❌ Installer build failed!"
    exit 1
fi
