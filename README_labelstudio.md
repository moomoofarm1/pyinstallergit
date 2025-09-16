# Label Studio Application with PyInstaller

A clean, minimal implementation of Label Studio with ML Backend, packaged as a standalone Windows executable using conda environment and PyInstaller.

## What This Is

- **Label Studio Frontend**: Web-based data annotation interface
- **Label Studio ML Backend**: Simple ML backend for predictions
- **Threading Architecture**: Frontend and ML backend run in separate threads
- **PyInstaller Packaging**: All dependencies bundled into a single Windows .exe file
- **Conda Environment**: Clean dependency management

## Prerequisites

- **Anaconda or Miniconda** installed on your system
- **Windows 10/11** (for building the .exe)
- **Git** for cloning the repository

## Step-by-Step Setup Guide

### Step 1: Install Anaconda/Miniconda

If you don't have conda installed:

1. **Download Miniconda** (lightweight option):
   - Go to: https://docs.conda.io/en/latest/miniconda.html
   - Download the Windows 64-bit installer
   - Run the installer and follow the prompts

2. **Verify installation**:
   ```cmd
   conda --version
   ```

### Step 2: Clone the Repository

1. **Clone the repository**:
   ```cmd
   git clone https://github.com/your-repo/gentofte.git
   cd gentofte
   ```

2. **Switch to the pyinstallerconda branch**:
   ```cmd
   git checkout pyinstallerconda
   ```

### Step 3: Set Up Conda Environment

The repository includes an `environment.yml` file that defines all necessary dependencies.

1. **View the environment configuration** (optional):
   ```cmd
   type environment.yml
   ```

2. **Create the conda environment**:
   ```cmd
   conda env create -f environment.yml
   ```
   This creates an environment named `labelstudio-env` with:
   - Python 3.9
   - Label Studio
   - Label Studio ML
   - PyInstaller
   - Required dependencies

3. **Activate the environment**:
   ```cmd
   conda activate labelstudio-env
   ```

4. **Verify the environment**:
   ```cmd
   conda list
   ```
   You should see `label-studio`, `label-studio-ml`, and `pyinstaller` in the list.

### Step 4: Build the Executable

1. **Run the automated build script**:
   ```cmd
   build_diarization.bat
   ```

   The build script will:
   - Verify conda is installed
   - Create/update the conda environment
   - Activate the environment
   - Install additional dependencies
   - Clean previous builds
   - Build the executable with PyInstaller
   - Verify the build

2. **Wait for completion**:
   - Build typically takes 2-5 minutes
   - You'll see progress messages
   - Success message will show file location and size

### Step 5: Run the Application

1. **Navigate to the dist folder**:
   ```cmd
   cd dist
   ```

2. **Run the executable**:
   ```cmd
   LabelStudioApp.exe
   ```

3. **Access the application**:
   - Open your browser
   - Go to: http://localhost:8080
   - You'll see the Label Studio interface

### Step 6: Configure ML Backend

1. **In Label Studio web interface**:
   - Create a new project
   - Go to Settings → Machine Learning
   - Click "Add Model"
   - Enter URL: `http://localhost:9090`
   - Click "Validate and Save"

2. **The ML backend provides**:
   - Simple prediction endpoint
   - Ready for customization
   - Integration with Label Studio

## File Structure

After setup, your directory will contain:

```
gentofte/
├── environment.yml           # Conda environment specification
├── labelstudio_app.py        # Main application source
├── labelstudio.spec         # PyInstaller configuration
├── build_diarization.bat    # Automated build script
├── dist/                    # Built executable location
│   └── LabelStudioApp.exe   # Your standalone application
├── build/                   # PyInstaller build cache
└── labelstudio_app.log      # Application logs
```

## Troubleshooting

### Conda Issues

**"conda is not recognized"**:
1. Restart Command Prompt after installing conda
2. Check if conda is in your PATH
3. Try using Anaconda Prompt instead

**Environment creation fails**:
1. Update conda: `conda update conda`
2. Clear conda cache: `conda clean --all`
3. Try creating manually: `conda create -n labelstudio-env python=3.9`

### Build Issues

**PyInstaller fails**:
1. Ensure you're in the activated conda environment
2. Check available disk space (need ~1GB)
3. Run Command Prompt as Administrator
4. Try building manually: `pyinstaller labelstudio.spec --clean`

**Missing dependencies**:
1. Activate environment: `conda activate labelstudio-env`
2. Install missing packages: `pip install package-name`
3. Re-run build script

### Runtime Issues

**Application won't start**:
1. Check if ports 8080 and 9090 are available
2. Close other applications using these ports
3. Check logs in `labelstudio_app.log`

**Browser won't connect**:
1. Wait 10-15 seconds after starting the application
2. Try refreshing the browser
3. Check Windows Firewall settings

## Customization

### Modifying the ML Backend

Edit `labelstudio_app.py`, find the `SimpleMLBackend` class:

```python
def predict(self, tasks, **kwargs):
    """Add your custom prediction logic here"""
    predictions = []
    for task in tasks:
        # Your ML code here
        predictions.append({
            "result": [],  # Your predictions
            "score": 0.0   # Confidence score
        })
    return predictions
```

### Adding Dependencies

1. **Edit `environment.yml`**:
   ```yaml
   dependencies:
     - python=3.9
     - pip
     - requests
     - your-new-package  # Add here
     - pip:
       - label-studio>=1.10.0
       - your-pip-package  # Or here for pip packages
   ```

2. **Rebuild the environment**:
   ```cmd
   conda env remove -n labelstudio-env
   conda env create -f environment.yml
   ```

3. **Rebuild the executable**:
   ```cmd
   build_diarization.bat
   ```

## Environment Management

### Useful Conda Commands

```cmd
# List all environments
conda env list

# Activate environment
conda activate labelstudio-env

# Deactivate environment
conda deactivate

# Remove environment
conda env remove -n labelstudio-env

# Export environment
conda env export > my_environment.yml

# Update environment
conda env update -f environment.yml
```

### Managing the Environment

**To update packages**:
```cmd
conda activate labelstudio-env
conda update --all
```

**To add new packages**:
```cmd
conda activate labelstudio-env
conda install package-name
# or
pip install package-name
```

**To export current environment**:
```cmd
conda activate labelstudio-env
conda env export > updated_environment.yml
```

## Production Deployment

### Sharing the Executable

1. **The .exe file is standalone**:
   - No Python installation required on target machines
   - No conda environment needed on target machines
   - All dependencies are bundled

2. **System requirements for end users**:
   - Windows 10/11
   - ~100MB disk space
   - Available ports 8080 and 9090

3. **Distribution**:
   - Copy `dist/LabelStudioApp.exe` to target machines
   - Optionally include usage instructions
   - No additional installation required

### Performance Notes

- **Startup time**: 10-30 seconds (includes server initialization)
- **Memory usage**: ~200-500MB
- **File size**: ~50-100MB executable
- **Network**: Only local connections (localhost)

## Support

For issues with this implementation:

1. **Check the logs**: Look at `labelstudio_app.log`
2. **Verify environment**: `conda activate labelstudio-env && conda list`
3. **Test manually**: Run `python labelstudio_app.py` for debugging
4. **Check ports**: Ensure 8080 and 9090 are available
5. **Review conda setup**: Ensure conda is properly installed and in PATH

This clean implementation focuses solely on Label Studio functionality with minimal dependencies for reliable PyInstaller packaging.