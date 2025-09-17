# PyInstaller Label Studio

A standalone executable package for Label Studio that includes both the frontend and ML backend components, built using PyInstaller.

## Features

- Bundles Label Studio frontend and ML backend into a single executable
- Automatic process management and monitoring
- Cross-platform support (Windows, macOS, Linux)
- Subprocess-based architecture for better isolation
- Automatic restart of failed services

## Installation

### Prerequisites

- Python 3.8 or higher
- Git

### Building the Executable

#### Windows
```bash
build.bat
```

#### macOS/Linux
```bash
./build.sh
```

## Usage

After building, run the executable from the `dist/` folder:

```bash
# Windows
dist/LabelStudioLauncher.exe

# macOS/Linux
./dist/LabelStudioLauncher
```

The application will start both services:
- Label Studio Frontend: http://localhost:8080
- Label Studio ML Backend: http://localhost:9090

Press `Ctrl+C` to stop all services.

## Project Structure

```
pyinstallerconda/
├── main.py              # Main launcher script
├── main.spec            # PyInstaller specification
├── requirements.txt     # Python dependencies
├── build.bat           # Windows build script
├── build.sh            # Unix build script
└── README.md           # This file
```

## Dependencies

- label-studio: Main annotation platform
- label-studio-ml-backend: ML backend for Label Studio
- pyinstaller: For creating standalone executables
- requests: HTTP client library
- psutil: Process management utilities

## Troubleshooting

If you encounter issues:

1. Ensure all dependencies are installed correctly
2. Check that no other services are running on ports 8080 or 9090
3. Verify Python 3.8+ is installed
4. For build issues, check the PyInstaller logs in the console output

## Development

To modify the launcher:

1. Edit `main.py` for functionality changes
2. Update `main.spec` for PyInstaller configuration changes
3. Rebuild using the build scripts

## License

This project is provided as-is for educational and development purposes.