#!/usr/bin/env python3
"""
ALF Label Studio Controller GUI

Provides a graphical interface to manage Label Studio and the ALF ML backend.
Handles installation, startup, registration, and cleanup of both services.
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
    """Main controller class for managing Label Studio and ALF ML backend."""
    
    def __init__(self):
        self.server_process = None
        self.label_studio_process = None
        self.root = None
        self.progress_bar = None
        self.status_label = None
        self.backend_registered = False
        self.project_root = Path(__file__).parent.parent

    # ========== ML Backend Management ==========
    
    def start_server(self):
        """Start the ALF ML backend server using uvicorn."""
        if self.server_process is not None:
            self.update_status("⚠️ Backend is already running")
            return
            
        try:
            server_path = self.project_root / "server.py"
            if not server_path.exists():
                self.update_status(f"❌ server.py not found in {self.project_root}")
                return
            
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "server:app",
                "--host", "0.0.0.0", "--port", "9090", "--reload"
            ], cwd=str(self.project_root), env=os.environ.copy(),
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.update_status("🚀 Starting ALF ML backend...")
            threading.Thread(target=self._wait_for_backend_startup, daemon=True).start()
            
        except Exception as e:
            self.update_status(f"❌ Failed to start backend: {e}")
            self.server_process = None
    
    def _wait_for_backend_startup(self):
        """Wait for the ML backend to be ready and attempt registration."""
        self.update_status("⏳ Waiting for ML backend to start...")
        
        for attempt in range(20):
            try:
                response = requests.get("http://localhost:9090/", timeout=3)
                if response.status_code == 200:
                    self.update_status("✅ ALF ML Backend is running on port 9090")
                    
                    if self._is_label_studio_running():
                        time.sleep(2)
                        self._register_backend()
                    else:
                        self.update_status("✅ Backend ready. Start Label Studio to auto-register.")
                    return
            except:
                pass
                
            time.sleep(2)
                    
        self.update_status("❌ Backend failed to start. Check console for errors.")
    
    def _register_backend(self):
        """Register the ALF ML backend with Label Studio."""
        try:
            self.update_status("🔗 Registering ML backend with Label Studio...")
            
            # Try CLI registration
            result = subprocess.run([
                sys.executable, "-m", "label_studio_ml",
                "init", "alf_backend", "--from", "http://localhost:9090", "--force"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.backend_registered = True
                self.update_status("✅ Backend registered successfully!")
                self._open_label_studio_delayed()
            else:
                self._register_via_api()
                
        except Exception as e:
            self.update_status(f"⚠️ Registration failed: {e}")
    
    def _register_via_api(self):
        """Alternative registration method using Label Studio's REST API."""
        try:
            ml_backend_config = {
                "url": "http://localhost:9090",
                "title": "ALF Whisper Backend",
                "description": "Whisper-based ASR backend for audio transcription"
            }
            
            response = requests.post("http://localhost:8080/api/ml/",
                                   json=ml_backend_config, timeout=10)
            
            if response.status_code in [200, 201]:
                self.backend_registered = True
                self.update_status("✅ Backend registered via API!")
                self._open_label_studio_delayed()
            else:
                self.update_status("✅ Backend running. Register manually in Label Studio.")
                
        except Exception:
            self.update_status("✅ Backend ready. Manual registration may be needed.")

    # ========== Label Studio Management ==========
    
    def install_label_studio(self):
        """Install Label Studio and label-studio-ml packages, then start."""
        self._show_progress()
        self.update_status("📦 Installing Label Studio...")
        threading.Thread(target=self._install_label_studio_task, daemon=True).start()
    
    def _install_label_studio_task(self):
        """Background task for Label Studio installation."""
        try:
            # Check if already installed
            result = subprocess.run([
                sys.executable, "-c", "import label_studio; print('installed')"
            ], capture_output=True, text=True)
            
            if "installed" not in result.stdout:
                packages = ["label-studio", "label-studio-ml"]
                for package in packages:
                    self.update_status(f"📦 Installing {package}...")
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "install", package
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode != 0:
                        raise Exception(f"Failed to install {package}")
            
            self._start_label_studio()
            
        except Exception as e:
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status(f"❌ Installation error: {e}"))
    
    def _start_label_studio(self):
        """Start the Label Studio server on port 8080."""
        try:
            self._kill_processes_on_port(8080)
            time.sleep(2)
            
            startup_commands = [
                ["label-studio", "start", "--port", "8080", "--host", "0.0.0.0"],
                [sys.executable, "-m", "label_studio", "start", "--port", "8080"]
            ]
            
            for cmd in startup_commands:
                try:
                    self.label_studio_process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        env=os.environ.copy())
                    
                    time.sleep(3)
                    if self.label_studio_process.poll() is None:
                        break
                except FileNotFoundError:
                    continue
            else:
                raise Exception("All startup methods failed")
            
            threading.Thread(target=self._wait_for_label_studio, daemon=True).start()
            
        except Exception as e:
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status(f"❌ Failed to start Label Studio: {e}"))
    
    def _wait_for_label_studio(self):
        """Wait for Label Studio to be ready and accessible."""
        self.root.after(0, lambda: self.update_status("⏳ Starting Label Studio..."))
        
        for attempt in range(40):
            if self._is_label_studio_running():
                self.root.after(0, self._hide_progress)
                self.root.after(0, lambda: self.update_status(
                    "✅ Label Studio started! Visit: http://localhost:8080"))
                
                threading.Thread(target=self._open_label_studio_delayed, daemon=True).start()
                
                if self.server_process is not None:
                    threading.Thread(target=self._register_backend, daemon=True).start()
                return
            
            if self.label_studio_process and self.label_studio_process.poll() is not None:
                self.root.after(0, self._hide_progress)
                self.root.after(0, lambda: self.update_status("❌ Label Studio process crashed"))
                return
                
            time.sleep(3)
            
        self.root.after(0, self._hide_progress)
        self.root.after(0, lambda: self.update_status("❌ Label Studio failed to start"))
    
    def _is_label_studio_running(self):
        """Check if Label Studio is running and accessible."""
        try:
            response = requests.get("http://localhost:8080", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _open_label_studio_delayed(self):
        """Open Label Studio in browser after a short delay."""
        time.sleep(2)
        webbrowser.open("http://localhost:8080")

    # ========== Cleanup and Shutdown ==========
    
    def stop_server_and_exit(self):
        """Stop all running processes and exit the application."""
        self.update_status("🛑 Shutting down...")
        
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
        
        self._kill_processes_on_port(9090)
        
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def uninstall_label_studio(self):
        """Stop Label Studio and uninstall all related packages."""
        self._show_progress()
        self.update_status("🛑 Stopping and removing Label Studio...")
        threading.Thread(target=self._uninstall_task, daemon=True).start()
    
    def _uninstall_task(self):
        """Background task for Label Studio uninstallation."""
        try:
            if self.label_studio_process:
                self.label_studio_process.terminate()
                self.label_studio_process = None
                time.sleep(2)
            
            self._kill_processes_on_port(8080)
            self._kill_processes_on_port(9090)
            
            packages = ["label-studio", "label-studio-ml"]
            for package in packages:
                try:
                    subprocess.run([sys.executable, "-m", "pip", "uninstall", package, "-y"],
                                 capture_output=True, text=True, timeout=60)
                except:
                    pass
            
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status("✅ Label Studio removed successfully!"))
            
        except Exception as e:
            self.root.after(0, self._hide_progress)
            self.root.after(0, lambda: self.update_status(f"⚠️ Cleanup error: {e}"))
    
    def _kill_processes_on_port(self, port):
        """Kill all processes using the specified port."""
        try:
            if platform.system() == 'Windows':
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
                try:
                    result = subprocess.run(['lsof', f'-ti:{port}'], 
                                          capture_output=True, text=True)
                    for pid in result.stdout.strip().split('\n'):
                        if pid.strip():
                            subprocess.run(['kill', '-9', pid.strip()], 
                                         capture_output=True)
                except:
                    subprocess.run(['pkill', '-f', f':{port}'], capture_output=True)
        except:
            pass

    # ========== Status and Utility Methods ==========
    
    def check_status(self):
        """Check and display the current status of both services."""
        ls_running = self._is_label_studio_running()
        
        backend_accessible = False
        try:
            response = requests.get("http://localhost:9090/", timeout=2)
            backend_accessible = response.status_code == 200
        except:
            pass
        
        status_parts = []
        status_parts.append("✅ Label Studio" if ls_running else "❌ Label Studio")
        status_parts.append("✅ ML Backend" if backend_accessible else "❌ ML Backend")
        
        status_msg = " | ".join(status_parts)
        
        if ls_running and backend_accessible:
            if self.backend_registered:
                status_msg += " | 🔗 Connected"
            else:
                status_msg += " | ⚠️ Not registered"
        
        self.update_status(status_msg)
    
    def update_status(self, message):
        """Update the status label with a new message."""
        if self.status_label:
            self.status_label.config(text=message)
        print(f"[ALF] {message}")
    
    def _show_progress(self):
        """Show the progress bar indicator."""
        self.progress_bar.pack(pady=5)
        self.progress_bar.start(10)
    
    def _hide_progress(self):
        """Hide the progress bar indicator."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
    
    def _debug_connections(self):
        """Debug method to check what's happening with connections."""
        print("\n" + "="*50)
        print("[ALF DEBUG] Connection Diagnostic")
        print("="*50)
        
        # Check processes
        if self.label_studio_process:
            poll_result = self.label_studio_process.poll()
            print(f"Label Studio process: {'Running' if poll_result is None else f'Exited with code {poll_result}'}")
        else:
            print("Label Studio process: Not started")
        
        if self.server_process:
            poll_result = self.server_process.poll()
            print(f"ML Backend process: {'Running' if poll_result is None else f'Exited with code {poll_result}'}")
        else:
            print("ML Backend process: Not started")
        
        # Check ports
        import socket
        for port, name in [(8080, "Label Studio"), (9090, "ML Backend")]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                print(f"Port {port} ({name}): {'OPEN' if result == 0 else 'CLOSED'}")
            except:
                print(f"Port {port} ({name}): ERROR checking")
        
        print("="*50)
        self.update_status("🔧 Debug info printed to console")

    # ========== GUI Creation and Management ==========
    
    def run_gui(self):
        """Create and run the main GUI application."""
        self.root = tk.Tk()
        self.root.title("🎯 ALF Label Studio Controller")
        self.root.geometry("520x500")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.stop_server_and_exit)
        
        # Title
        tk.Label(self.root, text="🎯 ALF Label Studio Controller", 
                font=("Arial", 16, "bold"), fg="#2C3E50").pack(pady=15)
        
        # Instructions
        tk.Label(self.root,
                text="Whisper-based ML Backend for Label Studio\n\n" +
                     "1️⃣ Install & Start Label Studio\n" +
                     "2️⃣ Start ALF ML Backend\n" +
                     "3️⃣ Use Label Studio with automatic transcription",
                font=("Arial", 11), justify="center", fg="#34495E").pack(pady=10)
        
        # Control buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=15)
        
        buttons = [
            ("1️⃣ Install & Start Label Studio", self.install_label_studio, "#27AE60", 2),
            ("2️⃣ Start ALF ML Backend", self.start_server, "#3498DB", 2),
            ("🔍 Check System Status", self.check_status, "#95A5A6", 1),
        ]
        
        for text, command, color, height in buttons:
            tk.Button(control_frame, text=text, command=command, width=40, height=height,
                     bg=color, fg="white", font=("Arial", 10, "bold"), relief="raised"
                     ).pack(pady=4)
        
        # Utility buttons
        utility_frame = tk.Frame(self.root)
        utility_frame.pack(pady=10)
        
        utility_buttons = [
            ("🌐 Open Label Studio", lambda: webbrowser.open("http://localhost:8080"), "#E67E22"),
            ("📚 Open Backend API Docs", lambda: webbrowser.open("http://localhost:9090/docs"), "#9B59B6"),
            ("🔧 Debug Connection Issues", self._debug_connections, "#34495E"),
            ("🗑️ Stop & Uninstall Everything", self.uninstall_label_studio, "#7F8C8D"),
        ]
        
        for text, command, color in utility_buttons:
            tk.Button(utility_frame, text=text, command=command, width=38, height=1,
                     bg=color, fg="white").pack(pady=2)
        
        # Stop button (prominent)
        tk.Button(utility_frame, text="🛑 Stop Backend & Exit", command=self.stop_server_and_exit,
                 width=38, height=2, bg="#E74C3C", fg="white", 
                 font=("Arial", 10, "bold")).pack(pady=8)
        
        # Progress bar (hidden by default)
        self.progress_bar = ttk.Progressbar(self.root, mode="indeterminate", length=400)
        
        # Status label
        self.status_label = tk.Label(self.root, text="Ready to start ALF", fg="#27AE60",
                                    font=("Arial", 10), wraplength=480)
        self.status_label.pack(pady=15)
        
        # Initial status check
        self.root.after(1000, self.check_status)
        self.root.mainloop()


# Entry point
def run_gui():
    """Main entry point for the GUI application."""
    controller = LabelStudioController()
    try:
        controller.run_gui()
    except tk.TclError as exc:
        # Gracefully handle environments without a display (e.g. CI/headless)
        print(f"Tkinter GUI cannot be started: {exc}")
        print("Running in headless mode – no GUI will be shown.")


if __name__ == "__main__":
    run_gui()
