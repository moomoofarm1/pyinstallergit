#!/usr/bin/env python3

import os
import sys
import subprocess

def create_directories():
    """Create the required directory structure"""
    dirs = ['front', 'back']
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created directory: {d}")

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Successfully installed requirements")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False
    return True

if __name__ == "__main__":
    print("Setting up ALF (Audio Label Frontend) project...")
    
    # Create directories
    create_directories()
    
    # Install requirements
    if install_requirements():
        print("\nSetup complete! You can now run:")
        print("python main.py")
    else:
        print("\nSetup failed. Please install requirements manually:")
        print("pip install -r requirements.txt")
