#!/usr/bin/env python3
"""
Set Git credentials for build_and_publish.py
This script creates a .env file with Git credentials
"""
import os
import sys
import getpass
from pathlib import Path


def set_credentials():
    """Set Git credentials"""
    print("SFTP GUI Manager - Set Git Credentials")
    print("=====================================")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    # Get credentials
    username = input("GitHub Username: ").strip()
    token = getpass.getpass("GitHub Personal Access Token: ").strip()
    
    if not username or not token:
        print("Error: Username and token are required")
        return False
        
    # Write to .env file
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"GIT_USERNAME={username}\n")
            f.write(f"GIT_TOKEN={token}\n")
            
        print(f"\n✅ Credentials saved to {env_file}")
        print("These credentials will be used by build_and_publish.py")
        print("\nNOTE: Keep this file secure and do not commit it to Git!")
        
        # Add to .gitignore if not already there
        gitignore_file = project_root / ".gitignore"
        if gitignore_file.exists():
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if ".env" not in content:
                with open(gitignore_file, 'a', encoding='utf-8') as f:
                    f.write("\n# Git credentials\n.env\n")
                print("Added .env to .gitignore")
        else:
            with open(gitignore_file, 'w', encoding='utf-8') as f:
                f.write("# Git credentials\n.env\n")
            print("Created .gitignore with .env entry")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = set_credentials()
    if not success:
        sys.exit(1)
