# Diarization Application

A standalone Windows executable for speaker diarization using Label Studio frontend and pyannote.audio ML backend.

## Features

- **Single Executable**: All dependencies bundled into one Windows .exe file
- **Label Studio Frontend**: Web-based annotation interface
- **Pyannote.audio Backend**: State-of-the-art speaker diarization
- **Threading Architecture**: Frontend and ML backend run in separate threads
- **No FastAPI Required**: Uses Label Studio ML SDK's built-in web server

## Architecture

The application consists of:

1. **Main Thread**: Orchestrates the entire application
2. **Frontend Thread**: Runs Label Studio web interface (port 8080)
3. **ML Backend Thread**: Runs pyannote.audio diarization service (port 9090)

## Prerequisites

### For Building
- Anaconda or Miniconda installed
- Windows 10/11
- At least 4GB RAM
- 2GB free disk space

### For Running
- HuggingFace token for pyannote.audio model access
- Windows 10/11

## Building the Executable

1. **Clone or download** the source code
2. **Open Command Prompt** in the project directory
3. **Run the build script**:
   ```cmd
   build_diarization.bat
   ```

The build script will:
- Create a conda environment with all dependencies
- Install Label Studio and pyannote.audio
- Build the executable using PyInstaller
- Create `dist/DiarizationApp.exe`

## Running the Application

1. **Set your HuggingFace token**:
   ```cmd
   set HF_TOKEN=your_huggingface_token_here
   ```

2. **Run the executable**:
   ```cmd
   dist\DiarizationApp.exe
   ```

3. **Open your browser** to http://localhost:8080

4. **Create a new project** in Label Studio for audio annotation

5. **Configure the ML backend**:
   - Go to Settings > Machine Learning
   - Add backend URL: `http://localhost:9090`

6. **Upload audio files** and start diarization

## Usage Instructions

1. **Project Setup**:
   - Create a new project in Label Studio
   - Choose "Audio" data type
   - Configure labeling interface for time series/speaker labels

2. **ML Backend Configuration**:
   - Navigate to project Settings
   - Go to Machine Learning tab
   - Click "Add Model"
   - Enter URL: `http://localhost:9090`
   - Click "Validate and Save"

3. **Audio Processing**:
   - Upload audio files (MP3, WAV, FLAC supported)
   - Click "Label" to start annotation
   - The ML backend will automatically generate speaker segments
   - Review and correct the predictions as needed

## Dependencies Included

- **label-studio**: Web-based data annotation tool
- **label-studio-ml**: ML backend SDK
- **pyannote.audio**: Speaker diarization toolkit
- **pytorch**: Deep learning framework
- **librosa**: Audio analysis library
- **soundfile**: Audio I/O library

## Troubleshooting

### Build Issues

1. **Conda not found**:
   - Install Anaconda/Miniconda
   - Restart Command Prompt
   - Ensure conda is in PATH

2. **PyInstaller errors**:
   - Check available disk space (need ~2GB)
   - Run Command Prompt as Administrator
   - Update PyInstaller: `pip install --upgrade pyinstaller`

3. **Missing dependencies**:
   - Delete the conda environment: `conda env remove -n diarization-env`
   - Re-run the build script

### Runtime Issues

1. **HF_TOKEN not set**:
   ```cmd
   set HF_TOKEN=your_token
   ```

2. **Port conflicts**:
   - Ensure ports 8080 and 9090 are available
   - Close other applications using these ports

3. **Audio file not loading**:
   - Supported formats: WAV, MP3, FLAC, M4A
   - Check file permissions
   - Ensure file path doesn't contain special characters

### Model Access Issues

1. **PyAnnote model download fails**:
   - Verify HF_TOKEN is valid
   - Check internet connection
   - Accept model license on HuggingFace website

2. **GPU not detected**:
   - Install CUDA-compatible PyTorch if GPU available
   - Application will fall back to CPU processing

## Technical Details

### Threading Model
- **Main Thread**: Application orchestration and user interface
- **Frontend Thread**: Label Studio web server (uvicorn/gunicorn)
- **Backend Thread**: ML model server (Label Studio ML SDK)

### Communication
- Frontend ↔ Backend: HTTP REST API
- Model predictions in Label Studio JSON format
- Real-time prediction updates

### Performance
- First prediction: ~10-30 seconds (model loading)
- Subsequent predictions: ~1-5 seconds per minute of audio
- Memory usage: ~2-4GB (depending on audio length)

## Development

To modify the application:

1. **Edit source files**:
   - `diarization_module.py`: Main application logic
   - `environment.yml`: Conda dependencies
   - `diarization.spec`: PyInstaller configuration

2. **Rebuild**:
   ```cmd
   build_diarization.bat
   ```

## License

This application bundles several open-source components:
- Label Studio: Apache 2.0 License
- PyAnnote.audio: MIT License
- PyTorch: BSD License

Ensure compliance with all component licenses for distribution.

## Support

For issues:
1. Check the troubleshooting section above
2. Review application logs (`diarization.log`)
3. Verify HuggingFace token and model access
4. Check system requirements and dependencies