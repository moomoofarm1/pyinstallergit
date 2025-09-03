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

## Deployment

### Standalone Executable (Windows 10+)

ALF can be packaged as a standalone .exe file that includes the GUI, audio processing libraries, and uv package manager. Users can run the executable without installing Python.

#### Build Process

**Windows:**
```batch
# Automated build
build.bat

# Manual build
pip install pyinstaller>=6.3 uv librosa soundfile pydub scipy numpy
pyinstaller alf_gui.spec --clean --noconfirm
```

**Linux/macOS:**
```bash
# Automated build  
./build.sh

# Manual build
pip install pyinstaller>=6.3 uv librosa soundfile pydub scipy numpy
pyinstaller alf_gui.spec --clean --noconfirm
```

#### Output
- **File**: `dist/ALF-AudioProcessing.exe` (~100-200MB)
- **Includes**: GUI, Python interpreter, audio libraries, uv package manager
- **Excludes**: ML frameworks (installed dynamically via GUI)

#### Deployment Strategy
1. **GUI + uv bundled**: Core application with package manager
2. **Dynamic ML installation**: Users click GUI buttons to install:
   - pyannote.audio (diarization) in isolated virtual environment
   - NeMo ASR (transcription) in separate virtual environment
3. **Clean separation**: No dependency conflicts between ML frameworks

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Branch Wrap-Up with PyInstaller

To complete and package this branch for distribution:

#### Prerequisites
1. **Clone or pull the production branch:**
   ```bash
   git clone https://github.com/moomoofarm1/pyinstallergit.git
   cd pyinstallergit
   git checkout production
   ```

2. **Ensure Python 3.9+ is installed** and available in PATH

#### Step-by-Step Packaging Process

1. **Install build dependencies:**
   ```bash
   # Core build tools
   pip install pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0
   
   # Runtime dependencies (minimal set)
   pip install uv librosa soundfile pydub scipy numpy requests pydantic pathlib2
   ```

2. **Verify uv installation:**
   ```bash
   # Install uv if not already available
   pip install uv
   
   # Verify uv is in PATH
   uv --version
   ```

3. **Create the standalone executable:**

   **Option A: Automated Build (Recommended)**
   ```batch
   # On Windows
   build.bat
   ```
   ```bash
   # On Linux/macOS
   chmod +x build.sh
   ./build.sh
   ```

   **Option B: Manual Build**
   ```bash
   # Clean previous builds
   rm -rf dist build version_info.txt  # Linux/macOS
   # rmdir /s /q dist build & del version_info.txt  # Windows
   
   # Build executable
   pyinstaller alf_gui.spec --clean --noconfirm
   ```

4. **Verify build success:**
   ```bash
   # Check if executable was created
   ls -la dist/ALF-AudioProcessing.exe  # Linux/macOS
   # dir dist\ALF-AudioProcessing.exe    # Windows
   
   # Test executable (optional)
   # Double-click or run from command line to verify GUI launches
   ```

5. **Package for distribution:**
   ```bash
   # Create distribution package
   mkdir ALF-Distribution
   cp dist/ALF-AudioProcessing.exe ALF-Distribution/
   cp readme.md DEPLOYMENT.md ALF-Distribution/
   
   # Create ZIP archive
   zip -r ALF-v0.2.0-Windows.zip ALF-Distribution/
   ```

#### What Gets Packaged
- **✅ Included in .exe (~100-200MB):**
  - Complete tkinter GUI application
  - Python 3.9+ interpreter
  - Audio processing libraries (librosa, soundfile, pydub)
  - uv package manager for dynamic installations
  - Configuration files and documentation

- **❌ NOT included (installed dynamically):**
  - pyannote.audio (diarization) - installed when user clicks setup
  - NeMo ASR (transcription) - installed when user clicks setup
  - PyTorch, FastAPI, Label Studio - installed on-demand

#### End User Experience
1. **Download** `ALF-AudioProcessing.exe` (single file)
2. **Run** executable (no Python installation required)
3. **Setup** virtual environments via GUI (one-time, ~5-10 minutes)
4. **Process** audio files using diarization and transcription pipelines
5. **Clean exit** removes all virtual environments when done

#### Troubleshooting
- **Build fails**: Check that all dependencies are installed and uv is in PATH
- **Large file size**: Normal for bundled Python application (~100-200MB)
- **Antivirus warnings**: Add exclusions for build directory and executable
- **Missing uv**: Will fallback to pip, but installation will be slower

This packaging approach provides a **professional, distributable application** that users can run without any Python setup while maintaining the flexibility to install ML components dynamically.

## Development Status

- ✅ **Audio Preprocessing**: Complete with comprehensive testing
- ✅ **Diarization Pipeline**: Complete with pyannote.audio integration
- ✅ **GUI and Communication**: Full-featured tkinter interface
- ✅ **Testing Framework**: Comprehensive unit and integration tests
- ✅ **PyInstaller Packaging**: Standalone executable with dynamic ML installation
- 🔄 **Transcription Pipeline**: Framework ready, awaiting NeMo ASR implementation
