"""
ALF Label Studio Controller GUI

This module provides a graphical interface to manage Label Studio and the ALF ML backend.
It handles installation, startup, registration, and cleanup of both services.

File Structure:
- main.py (root) - Entry point that calls run_gui()
- server.py (root) - FastAPI server wrapping the ML backend
- back/llm_backend.py - Whisper-based ML backend implementation
- front/gui.py (this file) - GUI controller

Usage:
    Run from main.py: python main.py
    Or directly: python front/gui.py
"""

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import sys
import os
import signal
import webbrowser
import time
import requests
from pathlib import Path
import platform


class LabelStudioController:
    """
    Main controller class for managing Label Studio and ALF ML backend.
    
    This class handles:
    - Label Studio installation and startup
    - ALF ML backend server management
    - Backend registration with Label Studio
    - Process cleanup and shutdown
    """
    
    def __init__(self):
        """Initialize the controller with default state."""
        # Process management
        self.server_process = None          # ALF ML backend process
        self.label_studio_process = None    # Label Studio server process
        
        # GUI components
        self.root = None                    # Main tkinter window
        self.progress_bar = None           # Progress indicator
        self.status_label = None           # Status message display
        
        # State tracking
        self.backend_registered = False    # Whether backend is registered with LS
        
        # Get project root directory (where main.py and server.py are located)
        self.project_root = Path(__file__).parent.parent
    
    # =========================================================================
    # ML Backend Management
    # =========================================================================
    
    def start_server(self):
        """
        Start the ALF ML backend server using uvicorn.
        
        This method:
        1. Locates server.py in the project root
        2. Starts the FastAPI server on port 9090
        3. Waits for server to be ready
        4. Attempts to register with Label Studio if it's running
        """
        if self.server_process is not None:
            self.update_status("⚠️ Backend is already running")
            return
            
        try:
            # Verify server.py exists
            server_path = self.project_root / "server.py"
            if not server_path.exists():
                self.update_status(f"❌ server.py not found in {self.project_root}")
                return
            
            # Prepare environment (preserve user's HF_TOKEN if set)
            env = os.environ.copy()
            
            # Start the FastAPI backend server
            self.server_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m", "uvicorn",
                    "server:app",                    # Import server.py app
                    "--host", "0.0.0.0",           # Accept connections from anywhere
                    "--port", "9090",              # ALF backend port
                    "--reload"                     # Auto-reload on code changes
                ],
                cwd=str(self.project_root),        # Set working directory to project root
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.update_status("🚀 Starting ALF ML backend...")
            
            # Wait for server to be ready in background thread
            threading.Thread(target=self._wait_for_backend_startup, daemon=True).start()
            
        except Exception as e:
            self.update_status(f"❌ Failed to start backend: {e}")
            self.server_process = None
    
    def _wait_for_backend_startup(self):
        """
        Wait for the ML backend to be ready and attempt registration.
        
        This method runs in a background thread and:
        1. Polls the backend until it responds
        2. Updates status when backend is ready
        3. Attempts registration if Label Studio is running
        """
        max_attempts = 60  # Increased timeout for slower systems
        self.update_status("⏳ Waiting for ML backend to start...")
        
        for attempt in range(max_attempts):
            try:
                # Try multiple endpoints to check if backend is ready
                endpoints_to_try = [
                    "http://localhost:9090/",
                    "http://localhost:9090/docs",
                    "http://127.0.0.1:9090/"
                ]
                
                backend_ready = False
                for endpoint in endpoints_to_try:
                    try:
                        response = requests.get(endpoint, timeout=5)
                        if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                            backend_ready = True
                            break
                    except:
                        continue
                
                if backend_ready:
                    self.update_status("✅ ALF ML Backend is running on port 9090")
                    
                    # If Label Studio is running, attempt registration
                    if self._is_label_studio_running():
                        time.sleep(3)  # Give backend more time to fully initialize
                        self._register_backend()
                    else:
                        self.update_status("✅ Backend ready. Start Label Studio to auto-register.")
                    return
                    
            except Exception as e:
                if attempt % 10 == 0:  # Log every 10th attempt
                    print(f"[ALF] Backend check attempt {attempt}: {e}")
                
            # Backend not ready yet, wait and retry
            if attempt < max_attempts - 1:
                time.sleep(3)  # Increased wait time
                    
        # Backend failed to start
        self.update_status("❌ Backend failed to start. Check console for errors.")
        print(f"[ALF] Backend process status: {self.server_process.poll() if self.server_process else 'Not started'}")
    
    def _register_backend(self):
        """
        Register the ALF ML backend with Label Studio.
        
        This method tries multiple registration approaches:
        1. Using label-studio-ml command line tool
        2. Using Label Studio REST API
        3. Graceful fallback with manual registration instructions
        """
        try:
            self.update_status("🔗 Registering ML backend with Label Studio...")
            
            # Method 1: Use label-studio-ml CLI tool
            result = subprocess.run([
                sys.executable, "-m", "label_studio_ml",
                "init", "alf_backend",
                "--from", "http://localhost:9090",
                "--force"  # Overwrite existing backend with same name
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.backend_registered = True
                self.update_status("✅ Backend registered successfully!")
                self._open_label_studio_delayed()
                return
                
            # Method 2: Try direct API registration
            self._register_via_api()
            
        except subprocess.TimeoutExpired:
            self.update_status("⚠️ Registration timed out, but backend is running")
        except Exception as e:
            self.update_status(f"⚠️ Registration failed: {e}")
    
    def _register_via_api(self):
        """
        Alternative registration method using Label Studio's REST API.
        
        This method directly calls Label Studio's API to add the ML backend,
        which can work when the CLI tool fails.
        """
        try:
            session = requests.Session()
            
            # Prepare backend configuration
            ml_backend_config = {
                "url": "http://localhost:9090",
                "title": "ALF Whisper Backend",
                "description": "Whisper-based ASR backend for audio transcription"
            }
            
            # Attempt to register via API
            response = session.post(
                "http://localhost:8080/api/ml/",
                json=ml_backend_config,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.backend_registered = True
                self.update_status("✅ Backend registered via API!")
                self._open_label_studio_delayed()
            else:
                self.update_status("✅ Backend running. Register manually in Label Studio.")
                
        except Exception:
            self.update_status("✅ Backend ready. Manual registration may be needed.")
    
    # =========================================================================
    # Label Studio Management
    # =========================================================================
    
    def install_label_studio(self):
        """
        Install Label Studio and label-studio-ml packages, then start Label Studio.
        
        This method:
        1. Shows progress indicator
        2. Checks if already installed
        3. Installs required packages
        4. Starts Label Studio server
        """
        self._show_progress()
        self.update_status("📦 Installing Label Studio...")
        
        # Run installation in background thread to avoid blocking GUI
        threading.Thread(target=self._install_label_studio_task, daemon=True).start()
    
    def _install_label_studio_task(self):
        """
        Background task for Label Studio installation.
        
        This method runs in a separate thread to avoid freezing the GUI
        during the installation process.
        """
        try:
            # Check if Label Studio is already installed
            result = subprocess.run([
                sys.executable, "-c", 
                "import label_studio; print('installed')"
            ], capture_output=True, text=True)
            
            if "installed" not in result.stdout:
                # Install required packages
                packages_to_install = [
                    ["pip", "install", "label-studio"],
                    ["pip", "install", "label-studio-ml"]
                ]
                
                for cmd in packages_to_install:
                    self.update_status(f"📦 Installing {cmd[2]}...")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode != 0:
                        # Try alternative installation method
                        alt_cmd = [sys.executable, "-m", "pip", "install", cmd[2]]
                        result = subprocess.run(alt_cmd, capture_output=True, text=True, timeout=300)
                        
                        if result.returncode != 0:
                            raise Exception(f"Failed to install {cmd[2]}: {result.stderr}")
            
            # Start Label Studio after successful installation
            self._start_label_studio()
            
        except subprocess.TimeoutExpired:
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status("❌ Installation timed out"))
        except Exception as e:
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status(f"❌ Installation error: {e}"))
    
    def _start_label_studio(self):
        """
        Start the Label Studio server on port 8080.
        
        This method:
        1. Kills any existing Label Studio processes
        2. Starts a new Label Studio instance
        3. Waits for it to be ready
        4. Opens it in the browser
        """
        try:
            # Clean up any existing processes on port 8080
            self._kill_processes_on_port(8080)
            time.sleep(3)
            
            # Try different Label Studio startup methods
            startup_commands = [
                # Method 1: Standard startup
                ["label-studio", "start", "--port", "8080", "--host", "0.0.0.0"],
                # Method 2: Alternative startup
                ["python", "-m", "label_studio.core.server", "--port", "8080"],
                # Method 3: Direct module call
                [sys.executable, "-m", "label_studio", "start", "--port", "8080"]
            ]
            
            for i, cmd in enumerate(startup_commands):
                try:
                    print(f"[ALF] Trying startup method {i+1}: {' '.join(cmd)}")
                    self.label_studio_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=os.environ.copy()
                    )
                    
                    # Give it a moment to start
                    time.sleep(5)
                    
                    # Check if process is still running (didn't crash immediately)
                    if self.label_studio_process.poll() is None:
                        print(f"[ALF] Label Studio process started with PID: {self.label_studio_process.pid}")
                        break
                    else:
                        print(f"[ALF] Startup method {i+1} failed")
                        if i < len(startup_commands) - 1:
                            continue
                        else:
                            raise Exception("All startup methods failed")
                            
                except FileNotFoundError:
                    print(f"[ALF] Command not found for method {i+1}")
                    if i < len(startup_commands) - 1:
                        continue
                    else:
                        raise Exception("Label Studio command not found")
            
            # Wait for Label Studio to be ready
            threading.Thread(target=self._wait_for_label_studio, daemon=True).start()
            
        except Exception as e:
            print(f"[ALF] Failed to start Label Studio: {e}")
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status(f"❌ Failed to start Label Studio: {e}"))
    
    def _wait_for_label_studio(self):
        """
        Wait for Label Studio to be ready and accessible.
        
        This method polls Label Studio until it responds, then:
        1. Updates the status
        2. Opens Label Studio in browser
        3. Registers the backend if it's already running
        """
        max_attempts = 120  # Increased timeout for slower systems
        self.root.after(0, lambda: self.update_status("⏳ Starting Label Studio..."))
        
        for attempt in range(max_attempts):
            # Try multiple ways to check if Label Studio is ready
            ls_ready = False
            
            # Method 1: Check main endpoint
            if self._is_label_studio_running():
                ls_ready = True
            
            # Method 2: Check if process is still running (not crashed)
            if not ls_ready and self.label_studio_process:
                if self.label_studio_process.poll() is None:  # Process still running
                    # Try a longer timeout for slower systems
                    try:
                        response = requests.get("http://localhost:8080", timeout=10)
                        if response.status_code == 200:
                            ls_ready = True
                    except:
                        pass
                else:
                    # Process has terminated
                    self.root.after(0, self._hide_progress)
                    self.root.after(0, lambda: self.update_status("❌ Label Studio process crashed"))
                    return
            
            if ls_ready:
                self.root.after(0, self._hide_progress)
                self.root.after(0, lambda: self.update_status(
                    "✅ Label Studio started! Visit: http://localhost:8080"
                ))
                
                # Open in browser
                threading.Thread(target=self._open_label_studio_delayed, daemon=True).start()
                
                # Register backend if it's already running
                if self.server_process is not None:
                    threading.Thread(target=self._register_backend, daemon=True).start()
                return
            
            # Log progress every 20 attempts
            if attempt % 20 == 0 and attempt > 0:
                print(f"[ALF] Still waiting for Label Studio... attempt {attempt}/{max_attempts}")
                self.root.after(0, lambda: self.update_status(f"⏳ Label Studio starting... ({attempt}/{max_attempts})"))
                
            time.sleep(3)  # Increased wait time
            
        # Timeout - check what went wrong
        self.root.after(0, self._hide_progress)
        
        # Provide more specific error information
        if self.label_studio_process and self.label_studio_process.poll() is None:
            self.root.after(0, lambda: self.update_status("⚠️ Label Studio is running but not responding. Try manually: http://localhost:8080"))
        else:
            self.root.after(0, lambda: self.update_status("❌ Label Studio failed to start. Check if port 8080 is available."))
    
    def _is_label_studio_running(self):
        """
        Check if Label Studio is running and accessible.
        
        Returns:
            bool: True if Label Studio responds on port 8080, False otherwise
        """
        try:
            # Try multiple endpoints and timeouts
            endpoints = [
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:8080/api/health",
                "http://localhost:8080/version"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=8)
                    if response.status_code in [200, 404, 302]:  # 404/302 might be OK for some endpoints
                        return True
                except:
                    continue
                    
            return False
        except:
            return False
    
    def _open_label_studio_delayed(self):
        """Open Label Studio in the default web browser after a short delay."""
        time.sleep(2)
        webbrowser.open("http://localhost:8080")
    
    # =========================================================================
    # Cleanup and Shutdown
    # =========================================================================
    
    def stop_server_and_exit(self):
        """
        Stop all running processes and exit the application.
        
        This method:
        1. Terminates the ML backend process
        2. Cleans up any processes on backend port
        3. Closes the GUI and exits
        """
        self.update_status("🛑 Shutting down...")
        
        # Stop ML backend process
        if self.server_process:
            try:
                if platform.system() == 'Windows':
                    self.server_process.terminate()
                else:
                    os.kill(self.server_process.pid, signal.SIGTERM)
                self.server_process = None
                time.sleep(1)
            except:
                pass
        
        # Clean up any remaining processes on backend port
        self._kill_processes_on_port(9090)
        
        # Close GUI
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def uninstall_label_studio(self):
        """
        Stop Label Studio and uninstall all related packages.
        
        This method provides a complete cleanup:
        1. Stops all Label Studio processes
        2. Stops the ML backend
        3. Uninstalls Label Studio packages
        4. Kills processes on both ports
        """
        self._show_progress()
        self.update_status("🛑 Stopping and removing Label Studio...")
        
        threading.Thread(target=self._uninstall_task, daemon=True).start()
    
    def _uninstall_task(self):
        """Background task for Label Studio uninstallation."""
        try:
            # Stop Label Studio process
            if self.label_studio_process:
                self.label_studio_process.terminate()
                self.label_studio_process = None
                time.sleep(2)
            
            # Kill processes on both ports
            self._kill_processes_on_port(8080)  # Label Studio
            self._kill_processes_on_port(9090)  # ML Backend
            
            # Uninstall packages
            packages = ["label-studio", "label-studio-ml"]
            for package in packages:
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", 
                        "uninstall", package, "-y"
                    ], capture_output=True, text=True, timeout=60)
                except:
                    pass  # Ignore errors during uninstallation
            
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status("✅ Label Studio removed successfully!"))
            
        except Exception as e:
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status(f"⚠️ Cleanup error: {e}"))
    
    def _kill_processes_on_port(self, port):
        """
        Kill all processes using the specified port.
        
        Args:
            port (int): Port number to clear
        """
        try:
            if platform.system() == 'Windows':
                # Windows: Use netstat and taskkill
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], 
                                             capture_output=True)
                            except:
                                pass
            else:
                # Unix-like: Use lsof and kill
                try:
                    result = subprocess.run(['lsof', f'-ti:{port}'], 
                                          capture_output=True, text=True)
                    for pid in result.stdout.strip().split('\n'):
                        if pid.strip():
                            subprocess.run(['kill', '-9', pid.strip()], 
                                         capture_output=True)
                except:
                    # Alternative method using pkill
                    subprocess.run(['pkill', '-f', f':{port}'], capture_output=True)
        except:
            pass  # Ignore errors in process cleanup
    
    # =========================================================================
    # Status and Utility Methods
    # =========================================================================
    
    def check_status(self):
        """
        Check and display the current status of both services.
        
        This method checks:
        - Label Studio accessibility (port 8080)
        - ML Backend accessibility (port 9090)
        - Updates the status display with current state
        """
        ls_running = self._is_label_studio_running()
        
        # Check if backend is accessible
        backend_accessible = False
        try:
            response = requests.get("http://localhost:9090/", timeout=2)
            backend_accessible = response.status_code == 200
        except:
            pass
        
        # Build status message
        status_parts = []
        if ls_running:
            status_parts.append("✅ Label Studio")
        else:
            status_parts.append("❌ Label Studio")
            
        if backend_accessible:
            status_parts.append("✅ ML Backend")
        else:
            status_parts.append("❌ ML Backend")
        
        status_msg = " | ".join(status_parts)
        
        # Add connection status
        if ls_running and backend_accessible:
            if self.backend_registered:
                status_msg += " | 🔗 Connected"
            else:
                status_msg += " | ⚠️ Not registered"
        
        self.update_status(status_msg)
    
    def update_status(self, message):
        """
        Update the status label with a new message.
        
        Args:
            message (str): Status message to display
        """
        if self.status_label:
            # Update GUI label
            self.status_label.config(
