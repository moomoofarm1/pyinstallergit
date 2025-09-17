# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PyInstaller-based Label Studio launcher that packages Label Studio frontend and ML backend into a standalone executable. The project uses a subprocess-based architecture for process isolation and automatic service restart capabilities.

## Build Commands

### Building the Executable

**Windows:**
```bash
build.bat
```

**macOS/Linux:**
```bash
./build.sh
```

Both scripts will:
1. Create a virtual environment if it doesn't exist
2. Install dependencies from requirements.txt
3. Clean previous builds
4. Run PyInstaller with main.spec configuration
5. Output executable to `dist/` folder

### Running the Application

After building:
```bash
# Windows
dist/LabelStudioLauncher.exe

# macOS/Linux
./dist/LabelStudioLauncher
```

## Architecture

### Core Components

- **main.py**: Main launcher script that manages Label Studio processes
  - `LabelStudioLauncher` class handles process lifecycle management
  - Starts backend first (port 9090), then frontend (port 8080)
  - Includes automatic process monitoring and restart functionality
  - Signal handling for clean shutdown

- **main.spec**: PyInstaller configuration
  - Collects all Label Studio and ML backend data files
  - Includes comprehensive hidden imports for Label Studio dependencies
  - Configured for console application with UPX compression

### Process Management

The launcher uses a subprocess-based architecture:
1. ML Backend starts first on port 9090 (`label_studio_ml.server`)
2. Frontend starts on port 8080 (`label_studio.server`)
3. Monitoring thread checks process health every 5 seconds
4. Automatic restart of failed processes
5. Clean shutdown with SIGINT/SIGTERM handling

### Dependencies

Core dependencies in requirements.txt:
- label-studio: Main annotation platform
- label-studio-ml-backend: ML backend services
- pyinstaller: Executable packaging
- requests: HTTP client
- psutil: Process utilities

## Development Workflow

1. Modify `main.py` for functionality changes
2. Update `main.spec` for PyInstaller configuration changes
3. Test locally by running `python main.py`
4. Rebuild executable using build scripts
5. Test executable from `dist/` folder

## Port Configuration

- Frontend: http://localhost:8080
- ML Backend: http://localhost:9090

Ensure these ports are available before running the application.