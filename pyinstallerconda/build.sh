#!/bin/bash

echo "Building Label Studio with PyInstaller..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build with PyInstaller
echo "Building executable..."
pyinstaller main.spec

echo "Build complete! Executable is in dist/ folder."

# Deactivate virtual environment
deactivate