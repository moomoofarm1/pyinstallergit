#!/bin/bash
# Build script for ALF GUI application on Linux/macOS
# This script creates a standalone executable with PyInstaller

echo "===================================="
echo "ALF - Advanced Audio Label Frontend"
echo "Build Script for Linux/macOS"
echo "===================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.9+ and ensure it's in PATH"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found. Please run this script from the project root directory."
    exit 1
fi

echo
echo "Step 1: Installing build dependencies..."
python3 -m pip install pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0

echo
echo "Step 2: Installing minimal runtime dependencies..."
python3 -m pip install librosa soundfile pydub scipy numpy requests pydantic pathlib2

echo
echo "Step 3: Installing uv package manager..."
python3 -m pip install uv

echo
echo "Step 4: Cleaning previous build..."
rm -rf dist build version_info.txt

echo
echo "Step 5: Creating application icon (if missing)..."
if [ ! -f "assets/alf_icon.ico" ]; then
    echo "Warning: Application icon not found at assets/alf_icon.ico"
    echo "The build will continue without a custom icon."
    echo "You can add an icon later by placing alf_icon.ico in the assets directory."
fi

echo
echo "Step 6: Building ALF executable..."
python3 -m pyinstaller alf_gui.spec --clean --noconfirm

echo
echo "Step 7: Verifying build..."
if [ -f "dist/ALF-AudioProcessing" ] || [ -f "dist/ALF-AudioProcessing.exe" ]; then
    echo "SUCCESS: ALF executable created successfully!"
    echo
    echo "Location: dist/ALF-AudioProcessing"
    echo "Size: $(du -h dist/ALF-AudioProcessing* | cut -f1)"
    echo
    echo "The executable includes:"
    echo "- Tkinter GUI application"
    echo "- Audio processing libraries"
    echo "- uv package manager (if available)"
    echo "- Python interpreter"
    echo
    echo "Users can run this executable without installing Python."
    echo "The GUI will allow installation of ML components in virtual environments."
else
    echo "ERROR: Build failed! ALF executable was not created."
    echo
    echo "Please check the build output above for errors."
    echo "Common issues:"
    echo "- Missing dependencies"
    echo "- Insufficient disk space"
    echo "- Permission issues"
    exit 1
fi

echo
echo "Step 8: Cleanup..."
rm -f version_info.txt

echo
echo "Build process completed successfully!"
echo "You can find the executable in the 'dist' directory."