# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ALF (Advanced Audio Label Frontend) is a comprehensive audio processing pipeline that provides:
- **Speaker Diarization** using pyannote.audio pipeline
- **Speech Transcription** using NeMo ASR models  
- **Audio Preprocessing** for format standardization
- **Browser-Server Architecture** with Label Studio integration
- **Virtual Environment Management** using uv

## Architecture

The refactored project follows a modular architecture with separate Browser-Server (B-S) structures:

### Core Components

1. **Entry Point**: `main.py` - Single Python file in root that starts the tkinter UI
2. **Audio Processing**: `audio_processing/` - MP3 to 16KHz mono preprocessing 
3. **Diarization Pipeline**: `diarization/` - pyannote.audio server and RTTM handling
4. **Transcription Pipeline**: `transcription/` - NeMo ASR with Label Studio ML backend
5. **Communication Layer**: `communication/` - JSON protocol and server management
6. **User Interface**: `ui/` - Tkinter GUI and pipeline controllers
7. **Testing Suite**: `tests/` - Comprehensive unit and integration tests

### Directory Structure

```
project_root/
├── main.py                     # Single entry point
├── audio_processing/           # Audio preprocessing pipeline
│   ├── preprocessing.py        # MP3 to 16KHz mono conversion
│   └── utils.py               # Audio utilities and validation
├── diarization/               # Speaker diarization B-S
│   ├── server.py             # FastAPI server with pyannote
│   ├── pipeline.py           # Diarization processing
│   └── rttm_handler.py       # RTTM file creation/parsing
├── transcription/            # Speech transcription B-S (future)
│   ├── server.py            # Label Studio ML backend
│   └── nemo_backend.py      # NeMo ASR implementation
├── communication/           # JSON-based communication
│   ├── json_protocol.py    # Message protocol definition  
│   └── server_manager.py   # Server lifecycle management
├── ui/                     # Tkinter interface
│   ├── main_window.py     # Main GUI application
│   └── pipeline_controller.py # Workflow coordination
├── tests/                 # Unit and integration tests
├── configs/              # Environment configurations
└── .venvs/              # Virtual environments (created by uv)
```

## Development Commands

### Environment Setup
```bash
# Setup virtual environments for different pipelines
uv venv .venvs/diarization --python 3.9
uv venv .venvs/transcription --python 3.9

# Install dependencies (handled by server manager)
# Dependencies listed in configs/diarization_env.txt and configs/transcription_env.txt
```

### Running the Application
```bash
python main.py           # Start the unified GUI controller
```

### Manual Server Commands
```bash
# Diarization server (runs in separate venv)
cd diarization && ../venvs/diarization/bin/python server.py

# Transcription server (runs in separate venv)  
cd transcription && ../venvs/transcription/bin/python server.py
```

### Testing
```bash
# Run unit tests
pytest tests/test_preprocessing.py -v
pytest tests/test_json_protocol.py -v

# Run all tests
pytest tests/ -v
```

### Configuration

#### Environment Variables
- `HF_TOKEN`: Hugging Face token for pyannote.audio models
- `ALF_SERVER_HOST`: Server host (default: 127.0.0.1)
- `ALF_SERVER_PORT`: Server port (9091 for diarization, 9092 for transcription)

#### Audio Processing Settings
- Input: MP3, WAV, FLAC, M4A files
- Output: 16KHz mono WAV files
- Processing directory: `processed_audio/`

## Ports and Services

- **Port 8080**: Label Studio frontend (external)
- **Port 9091**: Diarization server (pyannote.audio)
- **Port 9092**: Transcription server (NeMo ASR)
- **GUI**: Tkinter application (local)

## Key Dependencies

### Core Dependencies (main environment)
- `fastapi[standard]`: Web framework
- `uvicorn`: ASGI server
- `librosa`: Audio processing
- `soundfile`: Audio I/O
- `pydub`: Audio format conversion

### Diarization Environment (.venvs/diarization)
- `pyannote.audio>=3.0.0`: Speaker diarization
- `torch>=2.0.0`: Deep learning backend
- `scipy`: Signal processing

### Transcription Environment (.venvs/transcription)  
- `nemo-toolkit[asr]>=1.20.0`: Speech recognition
- `label-studio-ml>=1.0.9`: ML backend integration
- `omegaconf`: Configuration management

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

### 3. Transcription Pipeline  
- GUI starts transcription server in separate virtual environment
- Server uses NeMo ASR models via Label Studio ML backend
- Results include timestamped segments
- Browser opens Label Studio for transcription correction

### 4. JSON Communication
- All components communicate via standardized JSON protocol
- Message types: status, processing, progress, error
- Asynchronous processing with progress updates

## Important Implementation Notes

### Virtual Environment Isolation
- Diarization and transcription run in separate Python environments
- Prevents dependency conflicts between pyannote.audio and NeMo
- Managed automatically by ServerManager class

### Cross-Platform Compatibility
- Process management handles Windows/Unix differences
- Audio processing works across operating systems
- File paths use pathlib.Path for compatibility

### Error Handling and Logging
- Comprehensive logging to both file and GUI console
- Graceful degradation when dependencies unavailable
- Mock implementations for development/testing

### Testing Strategy
- Unit tests for individual components
- Integration tests for complete workflows  
- Mock implementations when heavy dependencies unavailable
- Automated CI/CD friendly test suite

## Troubleshooting

### Common Issues
1. **pyannote.audio model access**: Set HF_TOKEN environment variable
2. **Virtual environment setup**: Ensure uv is installed (`pip install uv`)
3. **Audio processing errors**: Check input file format and permissions
4. **Server startup failures**: Verify port availability and dependencies

### Development Tips
- Use mock implementations during development
- Check server logs for detailed error information
- Test audio preprocessing with small files first
- Monitor virtual environment dependencies separately