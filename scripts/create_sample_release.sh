#!/bin/bash

echo "SFTP GUI Manager - Create Sample Release"
echo "====================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    echo "Please install Python 3"
    exit 1
fi

# Parse arguments
VERSION=""
NO_DRY_RUN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="--version $2"
            shift 2
            ;;
        --no-dry-run)
            NO_DRY_RUN="--no-dry-run"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 scripts/create_sample_release.py $VERSION $NO_DRY_RUN"

echo "Running: $CMD"
eval $CMD

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sample release created successfully!"
else
    echo ""
    echo "❌ Failed to create sample release!"
    exit 1
fi
