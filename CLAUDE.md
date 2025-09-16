# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-component audio processing project with two main implementations:

1. **Simple Label Studio Integration** (`pyinstallergit/simplelabelstudio.py`) - Basic standalone file for testing
2. **ALF (Advanced Audio Label Frontend)** (`pyinstallergit/pyinstallergit/`) - Comprehensive audio processing pipeline with GUI

## Repository Structure

```
gentofte/
└── pyinstallergit/             # Main project directory
    ├── simplelabelstudio.py    # Simple Label Studio server implementation
    ├── build.bat              # Basic PyInstaller build script
    ├── tests/                 # Tests for simple implementation
    └── pyinstallergit/        # Advanced ALF implementation
        ├── main.py            # Entry point for GUI application
        ├── pyproject.toml     # Project configuration
        ├── build.bat          # Advanced build system
        ├── alf_gui.spec       # PyInstaller specification
        ├── audio_processing/  # Audio preprocessing pipeline
        ├── diarization/       # Speaker diarization server
        ├── transcription/     # Speech transcription (framework ready)
        ├── ui/                # Tkinter GUI interface
        ├── communication/     # JSON protocol layer
        ├── tests/             # Comprehensive test suite
        └── configs/           # Environment configurations
```

## Development Commands

### Simple Implementation
```bash
# Navigate to project directory
cd pyinstallergit

# Run simple Label Studio server
python simplelabelstudio.py

# Build simple executable
build.bat
```

### Advanced ALF Implementation
```bash
# Navigate to ALF directory
cd pyinstallergit/pyinstallergit

# Install dependencies with uv
uv sync

# Run full application
python main.py

# Run tests
pytest tests/ -v

# Build standalone executable (zero-dependency)
build.bat   # Windows
./build.sh  # Linux/macOS
```

## Key Architecture Components

### Simple Implementation
- **Single file**: `simplelabelstudio.py` - Basic Label Studio server
- **Basic build**: Standard PyInstaller configuration
- **Minimal dependencies**: Core Label Studio only

### Advanced ALF Implementation
- **Modular architecture**: Separate packages for each pipeline
- **Virtual environment isolation**: Prevents ML dependency conflicts
- **Browser-Server model**: FastAPI backends with Label Studio frontend
- **Zero-dependency build**: Automatic uv-based build system

## Build Systems

### Simple Build (`pyinstallergit/build.bat`)
```batch
python -m pip install --upgrade pyinstaller
pyinstaller --noconfirm --onefile simplelabelstudio.py
```

### Advanced Build (`pyinstallergit/pyinstallergit/build.bat`)
- **Zero prerequisites**: Automatically installs uv and Python 3.11
- **Isolated environments**: Uses uv for ultra-fast package management
- **Comprehensive bundling**: GUI + audio processing + package manager
- **Dynamic ML installation**: ML frameworks installed at runtime

## Testing

### Simple Implementation
```bash
cd pyinstallergit
pytest tests/test_simplelabelstudio.py -v
```

### Advanced Implementation
```bash
cd pyinstallergit/pyinstallergit
pytest tests/ -v

# Specific test modules
pytest tests/test_preprocessing.py -v
pytest tests/test_json_protocol.py -v
pytest tests/test_integration.py -v
```

## Environment Setup

### Simple Implementation
No special setup required - standard Python environment.

### Advanced Implementation
```bash
# Set Hugging Face token for pyannote.audio models
export HF_TOKEN=your_token_here

# Install uv package manager
pip install uv

# Dependencies managed automatically by build system
```

## Ports and Services

- **Port 8080**: Label Studio frontend (both implementations)
- **Port 9091**: Diarization server (ALF only)
- **Port 9092**: Transcription server (ALF only)

## Key Dependencies

### Simple Implementation
- `label-studio`: Annotation interface
- Basic Python standard library

### Advanced Implementation
- **Core**: `librosa`, `soundfile`, `pydub` (audio processing)
- **GUI**: `tkinter` (built-in Python GUI)
- **ML Frameworks**: Installed dynamically via uv
  - `pyannote.audio` (speaker diarization)
  - `nemo-toolkit` (speech recognition)
- **Package Management**: `uv` (ultra-fast Python package manager)

## Development Workflow

### For Simple Changes
Work directly with `simplelabelstudio.py` and use the basic build system.

### For Advanced Features
Navigate to `pyinstallergit/pyinstallergit/` directory and work with the modular architecture:

1. **Audio processing**: `audio_processing/preprocessing.py`
2. **Diarization**: `diarization/server.py` and `diarization/pipeline.py`
3. **GUI**: `ui/main_window.py`
4. **Communication**: `communication/json_protocol.py`

## Important Notes

### Virtual Environment Isolation (ALF)
- Each ML pipeline runs in a separate Python environment
- Automatic management via `communication/server_manager.py`
- Prevents conflicts between heavy ML frameworks

### Cross-Platform Compatibility
- Simple implementation: Basic cross-platform support
- ALF implementation: Comprehensive Windows/Linux/macOS support
- Path handling uses `pathlib.Path` throughout

### Build Strategy
- **Simple**: Traditional PyInstaller single-file executable
- **ALF**: Revolutionary zero-dependency build with dynamic ML installation
- **Deployment**: ALF creates ~100-200MB executable with GUI, users install ML components via GUI buttons

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure you're in the correct directory (`pyinstallergit/pyinstallergit/` for ALF)
2. **Build failures**: For ALF, run `cd pyinstallergit/pyinstallergit && build.bat` - everything installs automatically
3. **Virtual environment issues**: ALF automatically manages environments via uv
4. **Port conflicts**: Default ports 8080, 9091, 9092 - modify environment variables if needed

### Getting Help
- **Simple implementation**: Check `pyinstallergit/tests/test_simplelabelstudio.py` for usage examples
- **ALF implementation**: See `pyinstallergit/pyinstallergit/CLAUDE.md` for detailed technical documentation
- **Build issues**: Run build tests first: `cd pyinstallergit/pyinstallergit/build_tests && run_all_tests.bat`