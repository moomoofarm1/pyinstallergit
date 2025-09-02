# ALF - Advanced Audio Label Frontend

A comprehensive audio processing pipeline with speaker diarization and speech transcription capabilities using pyannote.audio and NeMo ASR, integrated with Label Studio for manual verification.

## Project Structure

```
project_root/
├── main.py                     # Single entry point - starts tkinter UI
├── pyproject.toml             # Modern Python project configuration
├── CLAUDE.md                  # Detailed development documentation
├── readme.md                  # This file
├── audio_processing/          # Audio preprocessing pipeline
│   ├── __init__.py
│   ├── preprocessing.py       # MP3 to 16KHz mono conversion
│   └── utils.py              # Audio utilities and validation
├── diarization/              # Speaker diarization Browser-Server
│   ├── __init__.py
│   ├── server.py            # FastAPI server with pyannote.audio
│   ├── pipeline.py          # Diarization processing logic
│   └── rttm_handler.py      # RTTM file creation and parsing
├── transcription/           # Speech transcription Browser-Server (framework ready)
│   ├── __init__.py
│   ├── server.py           # Label Studio ML backend (future)
│   └── nemo_backend.py     # NeMo ASR implementation (future)
├── communication/          # JSON-based inter-component communication
│   ├── __init__.py
│   ├── json_protocol.py   # Message protocol definitions
│   └── server_manager.py  # Server lifecycle management
├── ui/                    # Tkinter user interface
│   ├── __init__.py
│   ├── main_window.py    # Main GUI application
│   └── pipeline_controller.py # Workflow coordination
├── tests/                # Comprehensive test suite
│   ├── __init__.py
│   ├── test_preprocessing.py    # Audio processing tests
│   ├── test_json_protocol.py   # Communication tests
│   └── test_integration.py     # End-to-end tests
├── configs/              # Virtual environment configurations
│   ├── diarization_env.txt     # Diarization dependencies
│   └── transcription_env.txt   # Transcription dependencies
└── .venvs/               # Virtual environments (created at runtime)
    ├── diarization/      # pyannote.audio environment
    └── transcription/    # NeMo ASR environment
```

## Quick Start

### 1. **Install base dependencies:**
   ```bash
   # Install uv (modern Python package manager)
   pip install uv
   
   # Install base dependencies
   uv sync
   ```

### 2. **Start the application:**
   ```bash
   python main.py
   ```

### 3. **Set up environments (via GUI):**
   - The GUI will guide you through virtual environment setup
   - Or manually: Click "Setup All Environments" in the Environment Management tab

### 4. **Set Hugging Face token (for pyannote.audio models):**
   ```bash
   export HF_TOKEN=your_token_here
   ```

## Usage Workflow

### Audio Processing Pipeline

1. **Select Audio File**: Choose MP3, WAV, FLAC, or M4A files via the GUI
2. **Preprocess Audio**: Convert to 16KHz mono WAV format optimized for ML pipelines
3. **Choose Pipeline**:
   - **Diarization**: Identify speaker segments using pyannote.audio
   - **Transcription**: Convert speech to text using NeMo ASR (framework ready)

### Diarization Workflow

1. **Start Diarization Server**: Creates isolated virtual environment with pyannote.audio
2. **Process Audio**: Upload preprocessed audio for speaker diarization
3. **Review Results**: Opens Label Studio browser for manual verification of speaker segments
4. **Export RTTM**: Generate Rich Transcription Time Marked files for further processing

### Transcription Workflow (Framework Ready)

1. **Start Transcription Server**: Creates isolated environment with NeMo ASR
2. **Process Audio**: Upload preprocessed audio for speech recognition
3. **Review Results**: Opens Label Studio browser for transcription correction
4. **Export Text**: Generate timestamped transcriptions

## Key Features

### 🎯 **Modern Architecture**
- **Single Entry Point**: `main.py` launches comprehensive tkinter GUI
- **Modular Design**: Separate packages for audio processing, diarization, transcription
- **Virtual Environment Isolation**: Prevents dependency conflicts between ML frameworks

### 🔊 **Audio Processing**
- **Multi-format Support**: MP3, WAV, FLAC, M4A input files
- **Standardization**: Converts to 16KHz mono WAV for optimal ML performance
- **Quality Validation**: Checks audio integrity and provides processing statistics

### 🗣️ **Speaker Diarization**
- **pyannote.audio Integration**: State-of-the-art speaker diarization models
- **RTTM Output**: Industry-standard Rich Transcription Time Marked format
- **Label Studio Integration**: Browser-based manual verification interface

### 🎙️ **Speech Transcription** (Framework Ready)
- **NeMo ASR Integration**: NVIDIA's advanced speech recognition toolkit
- **Label Studio ML Backend**: Seamless annotation workflow integration
- **Timestamped Output**: Precise word and segment-level transcriptions

### 🔌 **Communication System**
- **JSON Protocol**: Standardized messaging between all components
- **Async Processing**: Non-blocking operations with progress updates
- **Error Handling**: Comprehensive error reporting and graceful degradation

### 🧪 **Testing & Quality**
- **Unit Tests**: Component-level validation with pytest
- **Integration Tests**: End-to-end workflow verification
- **Mock Support**: Development without heavy ML dependencies

## Ports and Services

- **Port 8080**: Label Studio frontend (external dependency)
- **Port 9091**: Diarization server (pyannote.audio FastAPI)
- **Port 9092**: Transcription server (NeMo ASR FastAPI - future)
- **GUI**: Tkinter application (local)

## Environment Configuration

### Automatic Setup (Recommended)
Use the GUI "Setup All Environments" button which automatically:
- Creates isolated virtual environments using `uv`
- Installs appropriate dependencies for each pipeline
- Configures server endpoints and communication

### Manual Setup
```bash
# Create diarization environment
uv venv .venvs/diarization --python 3.9
.venvs/diarization/bin/pip install -r configs/diarization_env.txt

# Create transcription environment (when ready)
uv venv .venvs/transcription --python 3.9
.venvs/transcription/bin/pip install -r configs/transcription_env.txt
```

## Advanced Usage

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_preprocessing.py -v
pytest tests/test_integration.py -v
```

### Development Mode
The system gracefully handles missing dependencies with mock implementations, allowing development without installing heavy ML frameworks.

### Cleanup and Exit
- **Standard Exit**: Stops servers, preserves virtual environments
- **Full Cleanup Exit**: Stops servers, removes all virtual environments and temporary files
- Use "Exit ALF (Remove Environments)" button for complete cleanup

## Troubleshooting

### Common Issues

1. **Virtual Environment Setup Fails**
   ```bash
   # Ensure uv is installed
   pip install uv
   ```

2. **pyannote.audio Model Access**
   ```bash
   # Set Hugging Face token for model access
   export HF_TOKEN=your_token_here
   ```

3. **Port Conflicts**
   - Default ports: 9091 (diarization), 9092 (transcription)
   - Modify `ALF_SERVER_PORT` environment variable if needed

4. **Audio Processing Errors**
   - Verify input file format (MP3, WAV, FLAC, M4A)
   - Check file permissions and disk space
   - Review logs in GUI console

### Getting Help

- **Documentation**: See `CLAUDE.md` for detailed technical documentation
- **Logs**: Check application logs in GUI console for detailed error information
- **Tests**: Run test suite to verify system integrity

## Technical Notes

- **Python 3.9+**: Required for compatibility with all ML frameworks
- **Cross-platform**: Tested on Windows, Linux, and macOS
- **Resource Requirements**: ~2GB RAM for basic operation, ~4GB for ML processing
- **Dependencies**: Automatically managed through virtual environments

## Development Status

- ✅ **Audio Preprocessing**: Complete with comprehensive testing
- ✅ **Diarization Pipeline**: Complete with pyannote.audio integration
- ✅ **GUI and Communication**: Full-featured tkinter interface
- ✅ **Testing Framework**: Comprehensive unit and integration tests
- 🔄 **Transcription Pipeline**: Framework ready, awaiting NeMo ASR implementation
