# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ALF (Advanced Audio Label Frontend) is a comprehensive audio processing application with the following core capabilities:
- **Speaker Diarization** using pyannote.audio pipeline
- **Speech Transcription** using NeMo ASR models (framework ready)
- **Audio Preprocessing** for format standardization (MP3 to 16KHz mono)
- **Browser-Server Architecture** with Label Studio integration
- **Virtual Environment Management** using uv package manager

## Architecture

The project follows a modular Browser-Server architecture with isolated virtual environments:

### Key Components

1. **Entry Point**: `main.py` - Single Python file that launches tkinter GUI
2. **Audio Processing**: `audio_processing/` - MP3 to 16KHz mono preprocessing pipeline
3. **Diarization Pipeline**: `diarization/` - pyannote.audio server with FastAPI and RTTM handling
4. **Transcription Pipeline**: `transcription/` - NeMo ASR with Label Studio ML backend (framework ready)
5. **Communication Layer**: `communication/` - JSON protocol and server lifecycle management
6. **User Interface**: `ui/` - Tkinter GUI with pipeline controllers
7. **Testing Suite**: `tests/` - Comprehensive unit and integration tests

### Virtual Environment Strategy
- **Main Environment**: GUI + audio processing + uv package manager
- **Diarization Environment**: `<temp>/alf_venvs/diarization` - pyannote.audio + torch (Label Studio removed)
- **Label Studio Environment**: `<temp>/alf_venvs/labelstudio` - label-studio + SDK (new mandatory separate environment)
- **Transcription Environment**: `<temp>/alf_venvs/transcription` - NeMo ASR + dependencies

This separation prevents dependency conflicts between heavy ML frameworks and provides mandatory Label Studio integration.

## Development Commands

### Environment Setup
```bash
# Install uv package manager (if not available)
pip install uv

# Install base dependencies
uv sync

# Set Hugging Face token for pyannote.audio models
export HF_TOKEN=your_token_here
```

### Running the Application
```bash
# Start from project root
python main.py
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_preprocessing.py -v
pytest tests/test_json_protocol.py -v
pytest tests/test_integration.py -v
```

### Building Standalone Executable
```bash
# Windows
build.bat

# Linux/macOS  
chmod +x build.sh
./build.sh
```

## Ports and Services

- **Port 8080**: Label Studio frontend (external dependency)
- **Port 9091**: Diarization server (pyannote.audio FastAPI)
- **Port 9092**: Transcription server (NeMo ASR FastAPI - future)
- **GUI**: Tkinter application (local)

## Key Dependencies

### Base Dependencies (main environment)
- `fastapi[standard]`: Web framework for servers
- `uvicorn`: ASGI server
- `librosa`, `soundfile`, `pydub`: Audio processing
- `tkinter`: GUI framework
- `requests`, `pydantic`: HTTP and data validation

### Diarization Environment (`<temp>/alf_venvs/diarization`)
- `pyannote.audio>=3.0.0`: Speaker diarization models
- `torch>=2.0.0`: Deep learning backend

### Label Studio Environment (`<temp>/alf_venvs/labelstudio`) 
- `label-studio>=1.10.0`: Annotation interface
- `label-studio-sdk>=0.0.32`: SDK for integration

### Transcription Environment (`<temp>/alf_venvs/transcription`)
- `nemo-toolkit[asr]>=1.20.0`: Speech recognition
- `label-studio-ml>=1.0.9`: ML backend integration

## Development Workflow

### 1. Audio Preprocessing
```python
from audio_processing.preprocessing import AudioPreprocessor

preprocessor = AudioPreprocessor()
output_file = preprocessor.preprocess_mp3_to_mono_16k("input.mp3")
```

### 2. Diarization Pipeline
- GUI starts diarization server in separate virtual environment
- Server processes audio using pyannote.audio
- Results saved as RTTM files
- Browser opens Label Studio for manual verification

### 3. Transcription Pipeline (Framework Ready)
- GUI starts transcription server in separate virtual environment  
- Server uses NeMo ASR models via Label Studio ML backend
- Results include timestamped segments
- Browser opens Label Studio for transcription correction

### 4. JSON Communication Protocol
- All components communicate via standardized JSON messages
- Message types: status, processing, progress, error
- Asynchronous processing with real-time progress updates

## Important Implementation Notes

### Virtual Environment Isolation
- Diarization, Label Studio, and transcription run in completely separate Python environments
- Prevents dependency conflicts between pyannote.audio, Label Studio, and NeMo
- Automatically managed by `ServerManager` class in `communication/server_manager.py`

### Cross-Platform Compatibility
- Process management handles Windows/Unix differences
- Audio processing works across all operating systems
- File paths use `pathlib.Path` for compatibility

### Error Handling and Testing
- Comprehensive logging to both file (`alf.log`) and GUI console
- Mock implementations for development without heavy ML dependencies
- Unit tests can run without installing pyannote.audio or NeMo

### PyInstaller Packaging
- Creates standalone ~100-200MB executable with GUI and uv bundled
- ML frameworks installed dynamically by user via GUI buttons
- Zero-dependency build process using uv standalone installer

## Environment Variables

- `HF_TOKEN`: Hugging Face token for accessing pyannote.audio models
- `ALF_SERVER_HOST`: Server host (default: 127.0.0.1)
- `ALF_SERVER_PORT`: Base server port (9091 for diarization, 9092 for transcription)

## Troubleshooting

### Common Issues
1. **pyannote.audio model access**: Set `HF_TOKEN` environment variable
2. **Virtual environment setup fails**: Ensure `uv` is installed (`pip install uv`)
3. **Audio processing errors**: Check input file format and file permissions
4. **Server startup failures**: Verify ports 9091/9092 are available
5. **Build failures**: Check that all dependencies are installed, run as administrator if needed

### Development Tips
- Use mock implementations during development to avoid installing heavy ML frameworks
- Check server logs in GUI console for detailed error information
- Test audio preprocessing with small files first
- Virtual environments are automatically cleaned up on application exit

## File Locations

### Key Source Files
- `main.py`: Application entry point
- `ui/main_window.py`: Main tkinter GUI
- `communication/server_manager.py`: Virtual environment and server management
- `audio_processing/preprocessing.py`: Audio format conversion
- `diarization/server.py`: FastAPI server for speaker diarization

### Configuration Files
- `pyproject.toml`: Modern Python project configuration
- `configs/diarization_env.txt`: Diarization environment dependencies
- `configs/labelstudio_env.txt`: Label Studio environment dependencies (new)
- `configs/transcription_env.txt`: Transcription environment dependencies
- `alf_gui.spec`: PyInstaller build specification

### Documentation
- `readme.md`: Comprehensive user guide
- `DEPLOYMENT.md`: Detailed build and deployment instructions