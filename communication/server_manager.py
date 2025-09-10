"""
Server Manager Module

This module manages the lifecycle of the various server components in the ALF system:
- Diarization server (pyannote.audio with FastAPI)
- Transcription server (NeMo ASR with Label Studio ML backend)
- Virtual environment management
- Process monitoring and control

The ServerManager handles server startup, shutdown, health checking, and configuration
for both the diarization and transcription pipelines.
"""

import os
import sys
import subprocess
import signal
import time
import logging
import shutil
import tempfile
try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    requests = None
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import threading
import json
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServerType(Enum):
    """Enumeration of server types."""
    DIARIZATION = "diarization"
    TRANSCRIPTION = "transcription"
    LABEL_STUDIO = "label_studio"

class ServerState(Enum):
    """Enumeration of server states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class ServerConfig:
    """Configuration for a server instance."""
    
    server_type: ServerType
    port: int
    host: str = "127.0.0.1"
    python_path: Optional[str] = None
    working_directory: Optional[Path] = None
    environment_variables: Optional[Dict[str, str]] = None
    startup_timeout: int = 30
    health_check_endpoint: str = "/health"

@dataclass
class ServerInfo:
    """Information about a running server."""
    
    server_type: ServerType
    state: ServerState
    pid: Optional[int] = None
    port: int = 0
    host: str = "127.0.0.1"
    uptime_seconds: float = 0.0
    last_health_check: Optional[str] = None
    error_message: Optional[str] = None

class ServerManager:
    """
    Manager class for controlling ALF server components.
    
    This class provides unified control over the diarization and transcription
    servers, including process management, health monitoring, and environment setup.
    """
    
    def __init__(self):
        """Initialize the server manager."""
        self.servers: Dict[ServerType, ServerInfo] = {}
        self.processes: Dict[ServerType, subprocess.Popen] = {}
        self.monitors: Dict[ServerType, threading.Thread] = {}
        self._shutdown_flag = threading.Event()
        
        # Default configurations
        self.configs = {
            ServerType.DIARIZATION: ServerConfig(
                server_type=ServerType.DIARIZATION,
                port=9091,
                working_directory=Path("diarization"),
                health_check_endpoint="/health",
                startup_timeout=120,
            ),
            ServerType.TRANSCRIPTION: ServerConfig(
                server_type=ServerType.TRANSCRIPTION,
                port=9092,
                working_directory=Path("transcription"),
                health_check_endpoint="/health"
            ),
            ServerType.LABEL_STUDIO: ServerConfig(
                server_type=ServerType.LABEL_STUDIO,
                port=8080,
                working_directory=Path("."),
                health_check_endpoint="/api/version",
                startup_timeout=60,
            )
        }
        
        # Virtual environment paths (use system temporary directory)
        self.venv_dir = Path(tempfile.gettempdir()) / "alf_venvs"
        self.diarization_venv = self.venv_dir / "diarization"
        self.transcription_venv = self.venv_dir / "transcription"
        self.label_studio_venv = self.venv_dir / "label_studio"

        logger.info("ServerManager initialized")
        if psutil is None or requests is None:
            missing = [name for name, mod in (('psutil', psutil), ('requests', requests)) if mod is None]
            logger.warning(
                "Missing optional packages: " + ", ".join(missing) +
                ". Install them via 'Setup All Environments' for full functionality."
            )

    def setup_virtual_environments(self):
        """
        Set up virtual environments for diarization, transcription, and Label Studio.
        
        This method creates separate virtual environments using uv for
        the different pipelines to avoid dependency conflicts.
        """
        logger.info("Setting up virtual environments...")
        
        try:
            # Create base temporary venv directory
            self.venv_dir.mkdir(exist_ok=True)

            # Setup diarization, label studio, and transcription environments
            self._setup_diarization_environment()
            self._setup_label_studio_environment()
            self._setup_transcription_environment()

            logger.info("Virtual environments setup completed")

        except Exception as e:
            logger.error(f"Virtual environment setup failed: {e}")
            raise RuntimeError(f"Cannot setup virtual environments: {e}")

    def _ensure_runtime_dependencies(self):
        """Ensure optional runtime dependencies are available."""
        missing = []
        if requests is None:
            missing.append("requests")
        if missing:
            raise RuntimeError(
                "Missing required packages: " + ", ".join(missing) +
                ". Please run 'Setup All Environments' to install dependencies."
            )
    
    def _get_uv_executable(self):
        """Get the path to uv executable, checking bundled location first."""
        # Check if running from PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled_uv = os.path.join(sys._MEIPASS, 'uv', 'uv.exe' if os.name == 'nt' else 'uv')
            if os.path.exists(bundled_uv):
                logger.info(f"Using bundled uv: {bundled_uv}")
                return bundled_uv

        # Check user-local installation first
        local_uv = os.path.expanduser("~/.local/bin/uv")
        if os.path.exists(local_uv) and os.access(local_uv, os.X_OK):
            logger.info(f"Using uv from: {local_uv}")
            return local_uv

        # Fall back to PATH lookup
        uv_path = shutil.which("uv")
        if uv_path:
            logger.info(f"Using system uv: {uv_path}")
            return uv_path

        raise RuntimeError("uv package manager not found. Please install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh")
    
    def _setup_diarization_environment(self):
        """Set up the diarization virtual environment."""
        logger.info("Setting up diarization environment...")
        
        try:
            # Get uv executable
            uv_exe = self._get_uv_executable()
            logger.info(f"Found uv executable at: {uv_exe}")
            
            # Create parent directory if it doesn't exist
            self.venv_dir.mkdir(exist_ok=True)
            logger.info(f"Created venv directory: {self.venv_dir}")
            
            # Create environment using uv
            cmd = [uv_exe, "venv", str(Path(self.diarization_venv)), "--python", "3.9"]
            logger.info(f"Creating virtual environment with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"uv venv creation failed. Return code: {result.returncode}")
                logger.error(f"stdout: {result.stdout}")
                logger.error(f"stderr: {result.stderr}")
                raise RuntimeError(f"Failed to create diarization venv: {result.stderr}")
            else:
                logger.info(f"Successfully created virtual environment at: {self.diarization_venv}")
                logger.info(f"uv output: {result.stdout}")
            
            # Install diarization dependencies using uv (faster than pip)
            python_path = Path(self.diarization_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
            
            # Base dependencies for diarization
            base_deps = [
                "fastapi[standard]>=0.100.0",
                "uvicorn>=0.23.0",
                "pyannote.audio>=3.0.0",
                "pyannote.core>=5.0.0",
                "torch>=2.0.0",
                "torchaudio>=2.0.0",
                "librosa>=0.10.0",
                "soundfile>=0.12.0",
                "requests>=2.31.0",
                "pydantic>=2.0.0"
            ]
            
            # Use uv to install dependencies in the venv
            deps_file = Path("configs/diarization_env.txt")
            if deps_file.exists():
                cmd = [uv_exe, "pip", "install", "-p", str(python_path), "-r", str(deps_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    logger.warning(f"uv installation failed, falling back to pip: {result.stderr}")
                    # Fallback to pip installation
                    self._install_deps_with_pip(self.diarization_venv, base_deps)
                else:
                    logger.info("Dependencies installed successfully with uv")
            else:
                logger.info("Installing diarization packages...")
                # Install all dependencies at once using uv (more efficient)
                cmd = [uv_exe, "pip", "install", "-p", str(python_path)] + base_deps
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout

                if result.returncode != 0:
                    logger.warning(f"Batch uv installation failed, trying individual pip installs: {result.stderr}")
                    # Fallback to pip installation one by one
                    self._install_deps_with_pip(self.diarization_venv, base_deps)
                else:
                    logger.info("All dependencies installed successfully with uv")
            
            logger.info("Diarization environment setup completed")
            
        except Exception as e:
            logger.error(f"Diarization environment setup failed: {e}")
            raise
    
    def _install_deps_with_pip(self, venv_path: Path, dependencies: list):
        """Install dependencies using pip as fallback."""
        pip_path = venv_path / ("Scripts/pip" if os.name == 'nt' else "bin/pip")
        
        for dep in dependencies:
            cmd = [str(pip_path), "install", dep]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Failed to install {dep}: {result.stderr}")
            else:
                logger.debug(f"Successfully installed: {dep}")

    def _setup_label_studio_environment(self):
        """Set up the Label Studio virtual environment."""
        logger.info("Setting up Label Studio environment...")

        try:
            uv_exe = self._get_uv_executable()

            # Create environment using uv
            cmd = [uv_exe, "venv", str(Path(self.label_studio_venv)), "--python", "3.9"]
            logger.info(f"Creating virtual environment with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to create Label Studio venv: {result.stderr}")
                raise RuntimeError(f"Failed to create Label Studio venv: {result.stderr}")

            python_path = Path(self.label_studio_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")

            logger.info("Installing Label Studio in its environment...")
            cmd = [uv_exe, "pip", "install", "-p", str(python_path), "label-studio>=1.10.0"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                logger.warning(f"uv installation failed, falling back to pip: {result.stderr}")
                self._install_deps_with_pip(self.label_studio_venv, ["label-studio>=1.10.0"])
            else:
                logger.info("Label Studio installed successfully with uv")

            logger.info("Label Studio environment setup completed")

        except Exception as e:
            logger.error(f"Label Studio environment setup failed: {e}")
            raise
    
    def _setup_transcription_environment(self):
        """Set up the transcription virtual environment."""
        logger.info("Setting up transcription environment...")
        
        try:
            # Get uv executable
            uv_exe = self._get_uv_executable()
            
            # Create environment using uv
            cmd = [uv_exe, "venv", str(Path(self.transcription_venv)), "--python", "3.9"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create transcription venv: {result.stderr}")
            
            # Install transcription dependencies using uv (faster than pip)
            python_path = Path(self.transcription_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
            
            # Use uv to install dependencies in the venv
            deps_file = Path("configs/transcription_env.txt")
            if deps_file.exists():
                cmd = [uv_exe, "pip", "install", "-p", str(python_path), "-r", str(deps_file)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.warning(f"uv installation failed, falling back to pip: {result.stderr}")
                    # Fallback to pip installation
                    self._install_deps_with_pip(self.transcription_venv, [
                        "label-studio-ml>=1.0.9",
                        "nemo-toolkit[asr]>=1.20.0",
                        "torch>=2.0.0",
                        "torchaudio>=2.0.0",
                        "omegaconf>=2.3.0",
                        "hydra-core>=1.3.0",
                        "librosa>=0.10.0",
                        "soundfile>=0.12.0",
                        "requests>=2.31.0",
                        "fastapi[standard]>=0.100.0",
                        "uvicorn>=0.23.0"
                    ])
                else:
                    logger.info("Dependencies installed successfully with uv")
            else:
                logger.warning("Dependencies file not found, installing individual packages")
                self._install_deps_with_pip(self.transcription_venv, [
                    "label-studio-ml>=1.0.9",
                    "nemo-toolkit[asr]>=1.20.0",
                    "torch>=2.0.0", 
                    "torchaudio>=2.0.0",
                    "omegaconf>=2.3.0",
                    "hydra-core>=1.3.0",
                    "librosa>=0.10.0",
                    "soundfile>=0.12.0",
                    "requests>=2.31.0",
                    "fastapi[standard]>=0.100.0",
                    "uvicorn>=0.23.0"
                ])
            
            logger.info("Transcription environment setup completed")
            
        except Exception as e:
            logger.error(f"Transcription environment setup failed: {e}")
            raise

    def check_environment_status(self) -> str:
        """
        Check the status of virtual environments.
        
        Returns:
            str: Status message describing environment state
        """
        status_parts = []
        
        # Check diarization environment
        if Path(self.diarization_venv).exists():
            python_path = Path(self.diarization_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
            if python_path.exists():
                status_parts.append("✓ Diarization env: Ready")
            else:
                status_parts.append("⚠ Diarization env: Incomplete")
        else:
            status_parts.append("✗ Diarization env: Not found")
        
        
        # Check transcription environment
        if Path(self.transcription_venv).exists():
            python_path = Path(self.transcription_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
            if python_path.exists():
                status_parts.append("✓ Transcription env: Ready")
            else:
                status_parts.append("⚠ Transcription env: Incomplete")
        else:
            status_parts.append("✗ Transcription env: Not found")
        
        return " | ".join(status_parts)

    def get_diarization_environment_info(self) -> dict:
        """
        Get detailed information about the diarization environment for debugging.
        
        Returns:
            dict: Detailed environment information
        """
        info = {
            "venv_base_dir": str(self.venv_dir),
            "diarization_venv_path": str(self.diarization_venv),
            "label_studio_venv_path": str(self.label_studio_venv),
            "venv_base_exists": self.venv_dir.exists(),
            "diarization_venv_exists": Path(self.diarization_venv).exists(),
            "label_studio_venv_exists": Path(self.label_studio_venv).exists(),
            "diarization_python_path": None,
            "diarization_python_exists": False,
            "label_studio_python_path": None,
            "label_studio_python_exists": False,
            "label_studio_installed": False,
            "uv_executable": None,
            "uv_available": False
        }

        # Check if python exists in diarization venv
        python_path = Path(self.diarization_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
        info["diarization_python_path"] = str(python_path)
        info["diarization_python_exists"] = python_path.exists()

        # Check python in Label Studio venv
        ls_python_path = Path(self.label_studio_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
        info["label_studio_python_path"] = str(ls_python_path)
        info["label_studio_python_exists"] = ls_python_path.exists()

        # Check if Label Studio is installed (in its own environment)
        if info["label_studio_python_exists"]:
            try:
                result = subprocess.run([str(ls_python_path), "-c", "import label_studio; print('installed')"],
                                      capture_output=True, text=True, timeout=5)
                info["label_studio_installed"] = (result.returncode == 0)
            except Exception:
                info["label_studio_installed"] = False
        
        # Check uv availability
        try:
            uv_exe = self._get_uv_executable()
            info["uv_executable"] = uv_exe
            info["uv_available"] = True
        except:
            info["uv_available"] = False
            
        return info
    
    def start_diarization_server(self, with_label_studio: bool = True) -> bool:
        """Start the diarization server.

        Parameters
        ----------
        with_label_studio: bool, optional
            If ``True`` (default), ensure the Label Studio frontend is also
            running. The frontend will be started even if the diarization
            backend fails to come up so that annotation can continue
            independently.

        Returns
        -------
        bool
            ``True`` if the diarization backend started successfully.
        """
        if not Path(self.diarization_venv).exists():
            logger.info("Diarization environment not found. Creating with uv...")
            self._setup_diarization_environment()

        success = self._start_server(ServerType.DIARIZATION)

        if with_label_studio:
            # Start Label Studio independently of the diarization backend
            if not self.start_label_studio_server():
                logger.error("Label Studio failed to start")
        if success and with_label_studio:
            # Start Label Studio in the same environment
            if not self._start_label_studio_server():
                logger.error("Label Studio failed to start")
                return False

        return success


    def start_label_studio_server(self) -> bool:
        """Public wrapper to start the Label Studio server.

        Ensures the Label Studio virtual environment exists before
        delegating to the internal startup routine.
        """
        if not Path(self.label_studio_venv).exists():
            logger.info("Label Studio environment not found. Creating with uv...")
            self._setup_label_studio_environment()

        return self._start_label_studio_server()


    def _start_label_studio_server(self) -> bool:
        """
        Start Label Studio server in its own virtual environment.
        
        Returns:
            bool: True if Label Studio started successfully
        """
        try:
            # Check if Label Studio is already running
            if self.is_server_running(ServerType.LABEL_STUDIO):
                logger.info("Label Studio server is already running")
                return True
            
            # Update server info
            self.servers[ServerType.LABEL_STUDIO] = ServerInfo(
                server_type=ServerType.LABEL_STUDIO,
                state=ServerState.STARTING,
                port=8080,
                host="127.0.0.1"
            )
            
            # Use python from Label Studio's own virtual environment
            python_path = Path(self.label_studio_venv) / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
            
            if not python_path.exists():
                raise FileNotFoundError(f"Python not found in Label Studio environment: {python_path}")
            
            # Create Label Studio project directory
            ls_project_dir = Path("label_studio_projects")
            ls_project_dir.mkdir(exist_ok=True)
            
            # Set up environment variables
            env = os.environ.copy()
            env['LABEL_STUDIO_PORT'] = '8080'
            env['LABEL_STUDIO_HOST'] = '127.0.0.1'
            env['LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED'] = 'true'
            env['LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT'] = str(Path.cwd())
            
            # Start Label Studio
            cmd = [
                str(python_path), "-m", "label_studio",
                "start", "diarization_project",
                "--host", "127.0.0.1",
                "--port", "8080",
                "--data-dir", str(ls_project_dir)
            ]
            
            logger.info(f"Starting Label Studio server with command: {' '.join(cmd)}")
            logger.info(f"Using Python path: {python_path}")
            logger.info(f"Working directory: {Path.cwd()}")
            logger.info(f"Label Studio project directory: {ls_project_dir}")
            
            process = subprocess.Popen(
                cmd,
                cwd=Path.cwd(),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[ServerType.LABEL_STUDIO] = process
            
            # Wait for Label Studio to start
            if self._wait_for_server_startup(ServerType.LABEL_STUDIO, 30):
                self.servers[ServerType.LABEL_STUDIO].state = ServerState.RUNNING
                self.servers[ServerType.LABEL_STUDIO].pid = process.pid
                
                # Start health monitoring
                self._start_health_monitor(ServerType.LABEL_STUDIO)
                
                logger.info(f"Label Studio server started successfully (PID: {process.pid})")
                logger.info("Label Studio should be accessible at http://127.0.0.1:8080")
                return True
            else:
                self.servers[ServerType.LABEL_STUDIO].state = ServerState.ERROR
                self.servers[ServerType.LABEL_STUDIO].error_message = "Label Studio failed to start within timeout"
                
                # Capture process output for debugging
                try:
                    stdout, stderr = process.communicate(timeout=2)
                    logger.error(f"Label Studio startup failed. Process stdout: {stdout}")
                    logger.error(f"Label Studio startup failed. Process stderr: {stderr}")
                except subprocess.TimeoutExpired:
                    logger.error("Label Studio process is still running but not responding to health checks")
                
                self._cleanup_failed_process(ServerType.LABEL_STUDIO)
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Label Studio server: {e}")
            if ServerType.LABEL_STUDIO in self.servers:
                self.servers[ServerType.LABEL_STUDIO].state = ServerState.ERROR
                self.servers[ServerType.LABEL_STUDIO].error_message = str(e)
            return False
    
    def start_transcription_server(self) -> bool:
        """
        Start the transcription server.

        Returns:
            bool: True if server started successfully
        """
        if not Path(self.transcription_venv).exists():
            logger.info("Transcription environment not found. Creating with uv...")
            self._setup_transcription_environment()

        return self._start_server(ServerType.TRANSCRIPTION)
    
    def _start_server(self, server_type: ServerType) -> bool:
        """
        Start a server of the specified type.
        
        Args:
            server_type (ServerType): Type of server to start
            
        Returns:
            bool: True if server started successfully
        """
        if self.is_server_running(server_type):
            logger.warning(f"{server_type.value} server is already running")
            return True

        try:
            self._ensure_runtime_dependencies()
            config = self.configs[server_type]
            
            # Update server info
            self.servers[server_type] = ServerInfo(
                server_type=server_type,
                state=ServerState.STARTING,
                port=config.port,
                host=config.host
            )
            
            # Prepare server startup
            python_path, server_script = self._prepare_server_startup(server_type)
            
            # Start the server process
            env = os.environ.copy()
            if config.environment_variables:
                env.update(config.environment_variables)
            
            # Set port in environment
            env['ALF_SERVER_PORT'] = str(config.port)
            env['ALF_SERVER_HOST'] = config.host
            
            cmd = [python_path, server_script]
            
            logger.info(f"Starting {server_type.value} server on {config.host}:{config.port}")
            
            process = subprocess.Popen(
                cmd,
                cwd=config.working_directory,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[server_type] = process
            
            # Wait for server to start
            if self._wait_for_server_startup(server_type, config.startup_timeout):
                self.servers[server_type].state = ServerState.RUNNING
                self.servers[server_type].pid = process.pid

                # Start health monitoring
                self._start_health_monitor(server_type)

                logger.info(f"{server_type.value} server started successfully (PID: {process.pid})")
                return True
            else:
                # Capture any output from the failed process for debugging
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except Exception:
                    stdout, stderr = "", ""

                if stdout:
                    logger.error(f"{server_type.value} server stdout:\n{stdout}")
                if stderr:
                    logger.error(f"{server_type.value} server stderr:\n{stderr}")

                self.servers[server_type].state = ServerState.ERROR
                self.servers[server_type].error_message = (
                    "Server failed to start within timeout. "
                    f"stdout: {stdout.strip()} stderr: {stderr.strip()}"
                )
                self._cleanup_failed_process(server_type)
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {server_type.value} server: {e}")
            self.servers[server_type] = ServerInfo(
                server_type=server_type,
                state=ServerState.ERROR,
                error_message=str(e)
            )
            return False
    
    def _prepare_server_startup(self, server_type: ServerType) -> Tuple[str, str]:
        """
        Prepare server startup parameters.
        
        Args:
            server_type (ServerType): Type of server to prepare
            
        Returns:
            Tuple[str, str]: Python path and server script path
        """
        if server_type == ServerType.DIARIZATION:
            venv = Path(self.diarization_venv)
            script = "server.py"
            script_rel = Path(server_type.value) / script
        elif server_type == ServerType.TRANSCRIPTION:
            venv = Path(self.transcription_venv)
            script = "server.py"
            script_rel = Path(server_type.value) / script
        elif server_type == ServerType.LABEL_STUDIO:
            # Label Studio uses its own separate virtual environment
            venv = Path(self.label_studio_venv)
            # Label Studio doesn't use a script file, handled separately
            return str(venv / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")), ""
        else:
            raise ValueError(f"Unknown server type: {server_type}")
        
        python_path = venv / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")

        # Determine actual script location (handles PyInstaller bundles)
        base_dir = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') else Path.cwd()
        script_path = base_dir / script_rel

        # Update working directory to script location
        self.configs[server_type].working_directory = script_path.parent

        if not python_path.exists():
            raise FileNotFoundError(f"Python not found in virtual environment: {python_path}")

        if not script_path.exists():
            raise FileNotFoundError(f"Server script not found: {script_path}")

        return str(python_path), str(script_path)
    
    def _wait_for_server_startup(self, server_type: ServerType, timeout: int) -> bool:
        """
        Wait for server to become ready.
        
        Args:
            server_type (ServerType): Type of server
            timeout (int): Timeout in seconds
            
        Returns:
            bool: True if server is ready
        """
        config = self.configs[server_type]
        url = f"http://{config.host}:{config.port}{config.health_check_endpoint}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(1)
        
        logger.error(f"{server_type.value} server failed to become ready within {timeout} seconds")
        return False
    
    def _start_health_monitor(self, server_type: ServerType):
        """Start health monitoring thread for a server."""
        if server_type in self.monitors and self.monitors[server_type].is_alive():
            return  # Monitor already running
        
        def monitor_health():
            config = self.configs[server_type]
            url = f"http://{config.host}:{config.port}{config.health_check_endpoint}"
            
            while not self._shutdown_flag.is_set() and self.is_server_running(server_type):
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        self.servers[server_type].last_health_check = time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        logger.warning(f"{server_type.value} server health check failed: {response.status_code}")
                        
                except requests.RequestException as e:
                    logger.warning(f"{server_type.value} server health check error: {e}")
                    
                time.sleep(30)  # Check every 30 seconds
        
        monitor_thread = threading.Thread(target=monitor_health, daemon=True)
        monitor_thread.start()
        self.monitors[server_type] = monitor_thread
    
    def stop_diarization_server(self, cleanup_venv=True) -> bool:
        """
        Stop the diarization server and optionally clean up the virtual environment.
        
        Args:
            cleanup_venv (bool): Whether to remove the virtual environment after stopping
        
        Returns:
            bool: True if server stopped successfully
        """
        success = True
        
        # Stop Label Studio first if it's running
        if self.is_server_running(ServerType.LABEL_STUDIO):
            logger.info("Stopping Label Studio server...")
            if not self._stop_server(ServerType.LABEL_STUDIO):
                success = False
        
        # Stop the diarization server
        if not self._stop_server(ServerType.DIARIZATION):
            success = False
        
        # Clean up virtual environment if requested
        if cleanup_venv and success:
            logger.info("Cleaning up diarization virtual environment...")
            self._cleanup_diarization_environment()
            logger.info("Cleaning up Label Studio virtual environment...")
            self._cleanup_label_studio_environment()
        
        return success

    def _cleanup_diarization_environment(self):
        """Clean up the diarization virtual environment."""
        try:
            venv_path = Path(self.diarization_venv)
            if venv_path.exists() and venv_path.is_dir():
                logger.info(f"Removing diarization virtual environment: {venv_path}")
                shutil.rmtree(str(venv_path))
                logger.info("Diarization virtual environment removed successfully")
            else:
                logger.info("No diarization virtual environment found to remove")

        except Exception as e:
            logger.error(f"Failed to remove diarization virtual environment: {e}")

    def _cleanup_label_studio_environment(self):
        """Clean up the Label Studio virtual environment."""
        try:
            venv_path = Path(self.label_studio_venv)
            if venv_path.exists() and venv_path.is_dir():
                logger.info(f"Removing Label Studio virtual environment: {venv_path}")
                shutil.rmtree(str(venv_path))
                logger.info("Label Studio virtual environment removed successfully")
            else:
                logger.info("No Label Studio virtual environment found to remove")

        except Exception as e:
            logger.error(f"Failed to remove Label Studio virtual environment: {e}")
    
    def stop_transcription_server(self) -> bool:
        """Stop the transcription server."""
        return self._stop_server(ServerType.TRANSCRIPTION)
    
    def _stop_server(self, server_type: ServerType) -> bool:
        """
        Stop a server of the specified type.
        
        Args:
            server_type (ServerType): Type of server to stop
            
        Returns:
            bool: True if server stopped successfully
        """
        if not self.is_server_running(server_type):
            logger.info(f"{server_type.value} server is not running")
            return True
        
        try:
            self.servers[server_type].state = ServerState.STOPPING
            
            process = self.processes.get(server_type)
            if process:
                logger.info(f"Stopping {server_type.value} server (PID: {process.pid})")
                
                # Try graceful shutdown first
                process.terminate()
                
                try:
                    process.wait(timeout=10)
                    logger.info(f"{server_type.value} server stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    logger.warning(f"Force killing {server_type.value} server")
                    process.kill()
                    process.wait()
                
                # Cleanup
                del self.processes[server_type]
            
            self.servers[server_type].state = ServerState.STOPPED
            self.servers[server_type].pid = None
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop {server_type.value} server: {e}")
            self.servers[server_type].state = ServerState.ERROR
            self.servers[server_type].error_message = str(e)
            return False
    
    def _cleanup_failed_process(self, server_type: ServerType):
        """Clean up a failed server process."""
        process = self.processes.get(server_type)
        if process:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    process.wait(timeout=5)
            except:
                pass
            finally:
                if server_type in self.processes:
                    del self.processes[server_type]
    
    def is_server_running(self, server_type: ServerType) -> bool:
        """
        Check if a server is running.
        
        Args:
            server_type (ServerType): Type of server to check
            
        Returns:
            bool: True if server is running
        """
        server_info = self.servers.get(server_type)
        if not server_info or server_info.state != ServerState.RUNNING:
            return False
        
        # Double-check process is actually running
        process = self.processes.get(server_type)
        if process and process.poll() is None:
            return True
        
        # Process died, update state
        if server_info:
            server_info.state = ServerState.STOPPED
            server_info.pid = None
        
        return False
    
    def is_diarization_running(self) -> bool:
        """Check if diarization server is running."""
        return self.is_server_running(ServerType.DIARIZATION)
    
    def is_transcription_running(self) -> bool:
        """Check if transcription server is running."""
        return self.is_server_running(ServerType.TRANSCRIPTION)
    
    def get_server_info(self, server_type: ServerType) -> Optional[ServerInfo]:
        """
        Get information about a server.
        
        Args:
            server_type (ServerType): Type of server
            
        Returns:
            Optional[ServerInfo]: Server information or None
        """
        return self.servers.get(server_type)
    
    def get_all_server_info(self) -> Dict[ServerType, ServerInfo]:
        """Get information about all servers."""
        return self.servers.copy()
    
    def cleanup_all(self):
        """Clean up all servers and resources."""
        logger.info("Cleaning up all servers...")
        
        # Set shutdown flag
        self._shutdown_flag.set()
        
        # Stop all servers
        for server_type in [ServerType.LABEL_STUDIO, ServerType.DIARIZATION, ServerType.TRANSCRIPTION]:
            if self.is_server_running(server_type):
                self._stop_server(server_type)
        
        # Wait for monitors to finish
        for monitor in self.monitors.values():
            if monitor.is_alive():
                monitor.join(timeout=5)
        
        self.monitors.clear()
        logger.info("Server cleanup completed")
    
    def cleanup_all_and_exit(self):
        """
        Clean up all servers, remove virtual environments, and prepare for application exit.
        
        This method performs a complete cleanup including:
        - Stopping all running servers
        - Removing virtual environments
        - Cleaning up temporary files
        """
        logger.info("Performing complete cleanup and exit preparation...")
        
        try:
            # First, cleanup all running servers
            self.cleanup_all()
            
            # Remove virtual environments
            self.remove_virtual_environments()
            
            logger.info("Complete cleanup finished - application ready to exit")
            
        except Exception as e:
            logger.error(f"Error during cleanup and exit: {e}")
            # Continue with cleanup even if there are errors
    
    def remove_virtual_environments(self):
        """
        Remove all virtual environments created by ALF.
        
        This method safely removes the temporary venv directory and all
        virtual environments within it.
        """
        try:
            import shutil
            
            if self.venv_dir.exists():
                logger.info(f"Removing virtual environments directory: {self.venv_dir}")
                
                # Remove the entire venv directory
                shutil.rmtree(str(self.venv_dir))
                
                logger.info("Virtual environments removed successfully")
            else:
                logger.info("No virtual environments directory found to remove")
                
        except Exception as e:
            logger.error(f"Failed to remove virtual environments: {e}")
            # Try to remove individual environments if full removal fails
            self._remove_individual_environments()
    
    def _remove_individual_environments(self):
        """Remove individual virtual environments if bulk removal fails."""
        try:
            import shutil
            
            environments = [self.diarization_venv, self.transcription_venv]
            
            for env_path in environments:
                if env_path.exists():
                    try:
                        logger.info(f"Removing individual environment: {env_path}")
                        shutil.rmtree(str(env_path))
                        logger.info(f"Successfully removed: {env_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to remove {env_path.name}: {e}")
            
            # Try to remove the parent venv directory if it's empty
            try:
                if self.venv_dir.exists() and not any(self.venv_dir.iterdir()):
                    self.venv_dir.rmdir()
                    logger.info("Removed empty venv directory")
            except Exception as e:
                logger.warning(f"Could not remove venv directory: {e}")
                
        except Exception as e:
            logger.error(f"Failed to remove individual environments: {e}")
    
    def restart_server(self, server_type: ServerType) -> bool:
        """
        Restart a server.
        
        Args:
            server_type (ServerType): Type of server to restart
            
        Returns:
            bool: True if restart was successful
        """
        logger.info(f"Restarting {server_type.value} server...")
        
        # Stop the server
        if not self._stop_server(server_type):
            logger.error(f"Failed to stop {server_type.value} server for restart")
            return False
        
        # Wait a moment
        time.sleep(2)
        
        # Start the server
        return self._start_server(server_type)
    
    def get_server_logs(self, server_type: ServerType, lines: int = 50) -> List[str]:
        """
        Get recent log lines from a server.
        
        Args:
            server_type (ServerType): Type of server
            lines (int): Number of recent lines to retrieve
            
        Returns:
            List[str]: List of log lines
        """
        process = self.processes.get(server_type)
        if not process:
            return []
        
        try:
            # This is a simplified implementation
            # In a real system, you'd want to use proper log files
            if process.stdout:
                # Read available output
                output_lines = []
                # Note: This is not ideal for production use
                # Consider using proper logging files instead
                return output_lines
            
        except Exception as e:
            logger.error(f"Failed to get logs for {server_type.value}: {e}")
        
        return []