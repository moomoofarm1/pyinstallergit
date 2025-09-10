# ALF Deployment Guide

This guide covers building and deploying the ALF (Advanced Audio Label Frontend) application as a standalone executable for Windows 10.

## Overview

The ALF application is packaged using PyInstaller to create a standalone executable that includes:
- Tkinter GUI application
- Python interpreter
- Audio processing libraries (librosa, soundfile, pydub)
- uv package manager (for dynamic ML component installation)
- Configuration files

The executable allows users to run ALF on Windows 10 without installing Python, and the GUI can dynamically install ML frameworks (pyannote.audio, NeMo ASR) in isolated virtual environments.

## Build Requirements

### Windows Build Environment
- **Windows 10** or later
- **Python 3.9+** installed and in PATH
- **Internet connection** for downloading dependencies
- **~2GB free disk space** for build process
- **Antivirus exclusions** for PyInstaller (recommended)

### Linux/macOS Build Environment (Cross-platform testing)
- **Python 3.9+** installed
- **Internet connection** for downloading dependencies
- **~2GB free disk space** for build process

## Building the Executable

### Method 1: Automated Build Script (Recommended)

#### On Windows:
```batch
# Navigate to project directory
cd /path/to/alf-project

# Run the build script
build.bat
```

#### On Linux/macOS:
```bash
# Navigate to project directory
cd /path/to/alf-project

# Make script executable (first time only)
chmod +x build.sh

# Run the build script
./build.sh
```

### Method 2: Manual Build Process

1. **Install build dependencies:**
   ```bash
   pip install pyinstaller>=6.3 pyinstaller-hooks-contrib>=2024.0
   ```

2. **Install runtime dependencies:**
   ```bash
   pip install librosa soundfile pydub scipy numpy requests pydantic pathlib2 uv
   ```

3. **Clean previous builds:**
   ```bash
   # Windows
   rmdir /s /q dist build
   del version_info.txt
   
   # Linux/macOS
   rm -rf dist build version_info.txt
   ```

4. **Build with PyInstaller:**
   ```bash
   pyinstaller alf_gui.spec --clean --noconfirm
   ```

## Build Configuration

### PyInstaller Spec File (`alf_gui.spec`)

The spec file is configured to:
- **Bundle uv executable** if available in PATH
- **Include configuration files** (configs/)
- **Include documentation** (README.md, CLAUDE.md)
- **Exclude heavy ML frameworks** (installed dynamically)
- **Create single-file executable** with UPX compression
- **Hide console window** (windowed application)

### Key Configuration Options

```python
# Application settings
APP_NAME = "ALF-AudioProcessing"
VERSION = "0.2.0"
CONSOLE = False  # Hide console window
ONE_FILE = True  # Single executable file
UPX = True      # Compression enabled
```

### Included Dependencies

**Core Libraries (bundled):**
- tkinter (GUI framework)
- librosa (audio processing)
- soundfile (audio I/O)
- pydub (audio conversion)
- scipy, numpy (scientific computing)
- requests (HTTP client)
- pydantic (data validation)

**Dynamic Libraries (installed by GUI):**
- pyannote.audio (speaker diarization)
- NeMo ASR (speech transcription)
- FastAPI/uvicorn (web frameworks)
- PyTorch/torchaudio (deep learning)

## Output Structure

After successful build:

```
dist/
└── ALF-AudioProcessing.exe    # Standalone executable (~100-200MB)

build/                         # Build artifacts (can be deleted)
version_info.txt              # Windows version info (temporary)
```

## Deployment

### Distribution Package

Create a deployment package:

```batch
# Create distribution directory
mkdir ALF-Distribution
copy dist\ALF-AudioProcessing.exe ALF-Distribution\
copy readme.md ALF-Distribution\
copy DEPLOYMENT.md ALF-Distribution\

# Create ZIP archive
powershell Compress-Archive -Path ALF-Distribution -DestinationPath ALF-v0.2.0-Windows.zip
```

### System Requirements (End Users)

**Minimum Requirements:**
- Windows 10 (64-bit)
- 4GB RAM
- 2GB free disk space (for virtual environments)
- Internet connection (for ML component installation)

**Recommended Requirements:**
- Windows 10/11 (64-bit)
- 8GB RAM
- 5GB free disk space
- Fast internet connection
- SSD for better performance

### Installation Instructions (End Users)

1. **Download** ALF-v0.2.0-Windows.zip
2. **Extract** to desired location (e.g., C:\ALF)
3. **Run** ALF-AudioProcessing.exe
4. **Allow firewall** access if prompted
5. **Setup environments** via GUI (one-time setup)

## Usage Workflow

### First-Time Setup
1. **Launch** ALF-AudioProcessing.exe
2. **Environment Setup** tab → "Setup All Environments"
3. **Wait** for virtual environment creation (~5-10 minutes)
4. **Set HF_TOKEN** environment variable (optional, for pyannote models)

### Audio Processing
1. **Select audio file** (MP3, WAV, FLAC, M4A)
2. **Preprocess** to 16KHz mono format
3. **Choose pipeline**:
   - Diarization (speaker identification)
   - Transcription (speech-to-text)
4. **Review results** in Label Studio browser

### Exit Options
- **Standard Exit**: Preserve virtual environments
- **Full Cleanup Exit**: Remove all environments and temp files

## Troubleshooting

### Build Issues

**Problem**: "uv not found in PATH"
**Solution**: Install uv separately:
```bash
pip install uv
```

**Problem**: "PyInstaller failed with ImportError"
**Solution**: Install missing dependencies:
```bash
pip install pyinstaller-hooks-contrib
```

**Problem**: "Antivirus blocking PyInstaller"
**Solution**: Add exclusions for:
- Project directory
- Python installation
- PyInstaller cache directory

### Runtime Issues

**Problem**: "Virtual environment creation failed"
**Solution**: 
- Check internet connection
- Verify disk space (>2GB)
- Run as administrator if needed

**Problem**: "Audio processing failed"
**Solution**:
- Check file format (MP3/WAV/FLAC/M4A)
- Verify file permissions
- Check disk space

**Problem**: "Server startup failed"
**Solution**:
- Check if ports 9090/9092 are available
- Verify virtual environments were created
- Check application logs

### Performance Optimization

**Reduce executable size:**
- Remove unused libraries from hiddenimports
- Disable UPX compression (upx=False)
- Use two-file mode instead of one-file

**Improve startup time:**
- Use two-file mode (faster startup)
- Reduce number of bundled libraries
- Optimize virtual environment creation

## Security Considerations

### Code Signing (Recommended for Distribution)

1. **Obtain code signing certificate**
2. **Sign the executable:**
   ```batch
   signtool sign /f certificate.p12 /p password /tr http://timestamp.server.com /td sha256 ALF-AudioProcessing.exe
   ```

### Antivirus Considerations

- **Test with major antivirus** solutions
- **Submit to VirusTotal** for false positive analysis
- **Consider reputation-based signing** for better detection rates

## Continuous Integration

### Automated Builds

Example GitHub Actions workflow:

```yaml
name: Build ALF Executable

on:
  push:
    tags: ['v*']

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Build executable
        run: build.bat
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: ALF-Windows
          path: dist/ALF-AudioProcessing.exe
```

## Version Management

### Version Updates

1. **Update version** in:
   - `pyproject.toml`
   - `alf_gui.spec`
   - `main.py`

2. **Update changelog**
3. **Test build process**
4. **Create release tag**

### Release Process

1. **Build and test** executable
2. **Create deployment package**
3. **Generate checksums**
4. **Upload to release page**
5. **Update documentation**

## Support and Maintenance

### Log Files

Application logs are stored in:
- **Runtime logs**: Application directory/alf.log
- **Build logs**: Console output during build

### Debugging

Enable debug mode by:
1. **Modify spec file**: `debug=True`
2. **Rebuild executable**
3. **Check console output**

### Updates

For updates:
1. **Download new version**
2. **Close current application**
3. **Replace executable**
4. **Restart application**
5. **Reconfigure if needed**

---

## Quick Reference

### Build Commands
```bash
# Windows
build.bat

# Linux/macOS
./build.sh

# Manual
pyinstaller alf_gui.spec --clean --noconfirm
```

### Key Files
- `alf_gui.spec` - PyInstaller configuration
- `build.bat/build.sh` - Build scripts
- `pyproject.toml` - Project configuration
- `configs/` - Environment dependencies

### Output
- `dist/ALF-AudioProcessing.exe` - Standalone executable
- Size: ~100-200MB
- Platforms: Windows 10+