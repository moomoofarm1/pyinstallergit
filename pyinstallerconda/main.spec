# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all label-studio data files and submodules
label_studio_datas = collect_data_files('label_studio')
label_studio_ml_datas = collect_data_files('label_studio_ml')

# Collect hidden imports
label_studio_imports = collect_submodules('label_studio')
label_studio_ml_imports = collect_submodules('label_studio_ml')

# Additional hidden imports that might be needed
hidden_imports = [
    'label_studio.server',
    'label_studio_ml.server',
    'uvicorn',
    'fastapi',
    'starlette',
    'pydantic',
    'sqlalchemy',
    'redis',
    'celery',
    'django',
    'psycopg2',
    'mysqlclient',
] + label_studio_imports + label_studio_ml_imports

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=label_studio_datas + label_studio_ml_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LabelStudioLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)