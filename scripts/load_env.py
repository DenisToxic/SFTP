"""
Load environment variables from .env file
This module is imported by build_and_publish.py
"""
import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent.parent / ".env"
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    
        return True
    return False


# Auto-load environment variables when imported
load_env()
