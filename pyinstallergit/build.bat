@echo off
REM Build simplelabelstudio.exe using PyInstaller
REM Ensure we're in the directory containing this script
cd /d "%~dp0"

REM Install PyInstaller if it's not already available
python -m pip install --upgrade pyinstaller >nul

REM Create a standalone executable in the dist folder
pyinstaller --noconfirm --onefile simplelabelstudio.py

echo.
echo Build complete. See the dist folder for simplelabelstudio.exe
