#!/usr/bin/env python3
"""
Create a sample release for testing
This script creates a sample release without building the application
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import build_and_publish module
from scripts.build_and_publish import BuildAndPublish
import scripts.load_env  # This will auto-load .env file


def create_sample_release(version=None, dry_run=True):
    """Create a sample release
    
    Args:
        version: Version to use (format: x.y.z)
        dry_run: If True, don't actually push to Git
    """
    print("SFTP GUI Manager - Create Sample Release")
    print("=======================================")
    
    builder = BuildAndPublish(
        version=version,
        dry_run=dry_run,
        skip_build=True,  # Skip building the application
        skip_git=False    # Don't skip Git operations
    )
    
    success = builder.run()
    
    if success:
        print("\n✅ Sample release created successfully!")
    else:
        print("\n❌ Failed to create sample release!")
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Create a sample release for testing")
    parser.add_argument("--version", help="Version to use (format: x.y.z)")
    parser.add_argument("--no-dry-run", action="store_true", help="Actually push to Git")
    
    args = parser.parse_args()
    
    create_sample_release(
        version=args.version,
        dry_run=not args.no_dry_run
    )


if __name__ == "__main__":
    main()
