#!/bin/bash

echo "SFTP GUI Manager - Set Git Credentials"
echo "====================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    echo "Please install Python 3"
    exit 1
fi

# Run the script
python3 scripts/set_git_credentials.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Git credentials set successfully!"
else
    echo ""
    echo "❌ Failed to set Git credentials!"
    exit 1
fi
