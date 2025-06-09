#!/bin/bash

echo "SFTP GUI Manager - Build and Publish"
echo "==================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    echo "Please install Python 3"
    exit 1
fi

# Parse arguments
VERSION=""
DRY_RUN=""
SKIP_BUILD=""
SKIP_GIT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="--version $2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --skip-build)
            SKIP_BUILD="--skip-build"
            shift
            ;;
        --skip-git)
            SKIP_GIT="--skip-git"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 scripts/build_and_publish.py $VERSION $DRY_RUN $SKIP_BUILD $SKIP_GIT"

echo "Running: $CMD"
eval $CMD

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build and publish completed successfully!"
else
    echo ""
    echo "❌ Build and publish failed!"
    exit 1
fi
