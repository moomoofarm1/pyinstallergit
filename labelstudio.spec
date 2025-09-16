# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Hidden imports for Label Studio and ML dependencies
hiddenimports = [
    'label_studio_ml',
    'label_studio_ml.model',
    'label_studio_ml.server',
    'label_studio_ml.utils',
    'requests',
    'uvicorn',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.websockets',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.logging',
    'tempfile',
    'pathlib',
    'threading',
    'subprocess',
    'json',
    'logging',
]

# Data files to include
datas = [
    # Include any configuration files if needed
]

a = Analysis(
    ['labelstudio_app.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'torch',
        'torchaudio',
        'librosa',
        'soundfile',
        'scipy',
        'numpy',
        'pyannote',
        'pydub',
    ],
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
    name='LabelStudioApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)