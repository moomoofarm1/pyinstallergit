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
import psutil
import requests
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
                health_check_endpoint="/health"
            ),
            ServerType.TRANSCRIPTION: ServerConfig(
                server_type=ServerType.TRANSCRIPTION,
                port=9092,
                working_directory=Path("transcription"),
                health_check_endpoint="/health"
            )
        }
        
        # Virtual environment paths
        self.venv_dir = Path(".venvs")
        self.diarization_venv = self.venv_dir / "diarization"
        self.transcription_venv = self.venv_dir / "transcription"
        
        logger.info("ServerManager initialized")
    
    def setup_virtual_environments(self):
        """
        Set up virtual environments for diarization and transcription.
        
        This method creates separate virtual environments using uv for
        the diarization and transcription pipelines to avoid dependency conflicts.
        """
        logger.info("Setting up virtual environments...")
        
        try:
            # Create .venvs directory
            self.venv_dir.mkdir(exist_ok=True)
            
            # Setup diarization environment
            self._setup_diarization_environment()
            
            # Setup transcription environment
            self._setup_transcription_environment()
            
            logger.info("Virtual environments setup completed")
            
        except Exception as e:
            logger.error(f"Virtual environment setup failed: {e}")
            raise RuntimeError(f"Cannot setup virtual environments: {e}")
    
    def _setup_diarization_environment(self):
        """Set up the diarization virtual environment."""
        logger.info("Setting up diarization environment...")
        
        # Create environment using uv
        cmd = ["uv", "venv", str(self.diarization_venv), "--python", "3.9"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create diarization venv: {result.stderr}")
        
        # Install diarization dependencies
        pip_path = self.diarization_venv / ("Scripts/pip" if os.name == 'nt' else "bin/pip")
        
        diarization_deps = [
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
        
        for dep in diarization_deps:
            cmd = [str(pip_path), "install", dep]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Failed to install {dep}: {result.stderr}")
        
        logger.info("Diarization environment setup completed")
    
    def _setup_transcription_environment(self):
        """Set up the transcription virtual environment."""
        logger.info("Setting up transcription environment...")
        
        # Create environment using uv
        cmd = ["uv", "venv", str(self.transcription_venv), "--python", "3.9"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create transcription venv: {result.stderr}")
        
        # Install transcription dependencies
        pip_path = self.transcription_venv / ("Scripts/pip" if os.name == 'nt' else "bin/pip")
        
        transcription_deps = [
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
        ]
        
        for dep in transcription_deps:
            cmd = [str(pip_path), "install", dep]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Failed to install {dep}: {result.stderr}")
        
        logger.info("Transcription environment setup completed")
    
    def check_environment_status(self) -> str:
        """
        Check the status of virtual environments.
        
        Returns:
            str: Status message describing environment state
        """
        status_parts = []
        
        # Check diarization environment
        if self.diarization_venv.exists():
            python_path = self.diarization_venv / ("Scripts/python" if os.name == 'nt' else "bin/python")
            if python_path.exists():
                status_parts.append("✓ Diarization env: Ready")
            else:
                status_parts.append("⚠ Diarization env: Incomplete")
        else:
            status_parts.append("✗ Diarization env: Not found")
        
        # Check transcription environment
        if self.transcription_venv.exists():
            python_path = self.transcription_venv / ("Scripts/python" if os.name == 'nt' else "bin/python")
            if python_path.exists():
                status_parts.append("✓ Transcription env: Ready")
            else:
                status_parts.append("⚠ Transcription env: Incomplete")
        else:
            status_parts.append("✗ Transcription env: Not found")
        
        return " | ".join(status_parts)
    
    def start_diarization_server(self) -> bool:
        """
        Start the diarization server.
        
        Returns:
            bool: True if server started successfully
        """
        return self._start_server(ServerType.DIARIZATION)
    
    def start_transcription_server(self) -> bool:
        """
        Start the transcription server.
        
        Returns:
            bool: True if server started successfully
        """
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
                self.servers[server_type].state = ServerState.ERROR
                self.servers[server_type].error_message = "Server failed to start within timeout"
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
            venv = self.diarization_venv
            script = "server.py"
        else:  # TRANSCRIPTION
            venv = self.transcription_venv  
            script = "server.py"
        
        python_path = venv / ("Scripts/python" if os.name == 'nt' else "bin/python")
        
        if not python_path.exists():
            raise FileNotFoundError(f"Python not found in virtual environment: {python_path}")
        
        script_path = Path(server_type.value) / script
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
    
    def stop_diarization_server(self) -> bool:
        """Stop the diarization server."""
        return self._stop_server(ServerType.DIARIZATION)
    
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
        for server_type in [ServerType.DIARIZATION, ServerType.TRANSCRIPTION]:
            if self.is_server_running(server_type):
                self._stop_server(server_type)
        
        # Wait for monitors to finish
        for monitor in self.monitors.values():
            if monitor.is_alive():
                monitor.join(timeout=5)
        
        self.monitors.clear()
        logger.info("Server cleanup completed")
    
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