# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ALF GUI application.

This spec file creates a standalone Windows executable containing:
- Tkinter GUI application
- uv package manager
- Minimal Python dependencies
- Audio processing libraries

The resulting .exe can run on Windows 10 without Python installed and
can dynamically install ML frameworks using uv in virtual environments.
"""

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

# Build configuration
APP_NAME = "ALF-AudioProcessing"
VERSION = "0.2.0"
DESCRIPTION = "Advanced Audio Label Frontend - GUI Application"

# Paths
project_root = Path(SPECPATH)
src_path = project_root

# Get uv executable path
uv_executable = None
try:
    import subprocess
    result = subprocess.run(['where', 'uv'] if sys.platform == 'win32' else ['which', 'uv'], 
                          capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        uv_executable = result.stdout.strip().split('\n')[0]
        print(f"Found uv executable: {uv_executable}")
    else:
        print("Warning: uv executable not found in PATH")
except Exception as e:
    print(f"Error finding uv executable: {e}")

# Data files to include
datas = [
    # Include configuration files
    ('configs', 'configs'),
    # Include README and documentation
    ('readme.md', '.'),
    ('CLAUDE.md', '.'),
]

# Include diarization server resources
datas += collect_data_files('diarization', include_py_files=True)

# Include uv executable if found
binaries = []
if uv_executable and os.path.exists(uv_executable):
    binaries.append((uv_executable, 'uv'))
    print(f"Including uv binary: {uv_executable}")
else:
    print("Warning: uv binary will not be included - users must install uv separately")

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    # Tkinter and GUI
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    
    # Audio processing
    'librosa',
    'soundfile',
    'scipy',
    'scipy.special',
    'scipy.special._cdflib',
    'numpy',
    'pydub',
    
    # Communication and utilities
    'requests',
    'json',
    'pathlib',
    'threading',
    'subprocess',
    'logging',
    'tempfile',
    'shutil',
    
    # Our modules
    'audio_processing',
    'audio_processing.preprocessing',
    'audio_processing.utils',
    'communication',
    'communication.json_protocol',
    'communication.server_manager',
    'ui',
    'ui.main_window',
    'ui.pipeline_controller',
    
    # Pydantic for data validation
    'pydantic',
    'pydantic.dataclasses',
    
    # Standard library modules that might be missed
    'uuid',
    'datetime',
    'enum',
    'dataclasses',
    'typing',
    'collections',
    'functools',
    'itertools',
    'operator',
    'os.path',
    'platform',
    'signal',
    'time',
    'webbrowser',
    'tzdata',
    'zoneinfo',
]

# Excludes - modules we don't want to include
excludes = [
    # Large ML frameworks (will be installed by uv)
    'torch',
    'torchaudio',
    'transformers',
    'pyannote',
    'nemo_toolkit',
    'fastapi',
    'uvicorn',
    'label_studio',
    
    # Development tools
    'pytest',
    'black',
    'ruff',
    'mypy',
    
    # Jupyter and IPython
    'IPython',
    'jupyter',
    'notebook',
    
    # Other heavy packages
    'matplotlib',
    'seaborn',
    'pandas',
    'sklearn',
    'tensorflow',
    'keras',
]

# Analysis phase
a = Analysis(
    ['main.py'],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Version information for Windows (create file before EXE())
version_info = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({VERSION.replace('.', ', ')}, 0),
    prodvers=({VERSION.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'ALF Development Team'),
            StringStruct('FileDescription', '{DESCRIPTION}'),
            StringStruct('FileVersion', '{VERSION}'),
            StringStruct('InternalName', '{APP_NAME}'),
            StringStruct('LegalCopyright', 'Copyright (c) 2024 ALF Team'),
            StringStruct('OriginalFilename', '{APP_NAME}.exe'),
            StringStruct('ProductName', '{APP_NAME}'),
            StringStruct('ProductVersion', '{VERSION}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)"""

# Write version info file BEFORE EXE() constructor uses it
try:
    with open('version_info.txt', 'w') as f:
        f.write(version_info)
    print("Created version_info.txt for Windows executable metadata")
except Exception as e:
    print(f"Warning: Could not create version_info.txt: {e}")

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
    icon='assets/alf_icon.ico' if os.path.exists('assets/alf_icon.ico') else None,
)


print(f"""
PyInstaller Spec Configuration Summary:
======================================
Application: {APP_NAME}
Version: {VERSION}
Description: {DESCRIPTION}

Configuration:
- Console: Hidden (windowed application)
- One file: Yes (single .exe)
- UPX compression: Yes
- Include uv: {'Yes' if uv_executable else 'No (install separately)'}

Output: dist/{APP_NAME}.exe

Build command:
pyinstaller alf_gui.spec --clean --noconfirm

The resulting .exe will:
1. Run the tkinter GUI on Windows 10
2. Allow users to install ML components via GUI buttons
3. Use uv to create isolated virtual environments
4. Support complete audio processing workflows
""")