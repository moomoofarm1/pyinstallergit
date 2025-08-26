import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import os
import signal
import webbrowser
import time
import shutil
import json
import requests
from pathlib import Path
import platform

class LabelStudioController:
    def __init__(self):
        self.server_process = None
        self.label_studio_process = None
        self.root = None
        self.progress_bar = None
        self.status_label = None
        self.backend_registered = False
        
    def start_server(self):
        """Start the ML backend server"""
        if self.server_process is None:
            try:
                # Forward the current environment so a user-set HF_TOKEN is respected
                env = os.environ.copy()
                
                # Start FastAPI backend server
                self.server_process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "server:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "9090",
                    ],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.update_status("🚀 ML Backend starting...")
                
                # Check if server is ready and then register
                threading.Thread(target=self.wait_and_register_backend, daemon=True).start()
                
            except Exception as e:
                self.update_status(f"❌ Failed to start server: {e}")

    def wait_and_register_backend(self):
        """Wait for backend to be ready and register it with Label Studio"""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:9090/health", timeout=2)
                if response.status_code == 200:
                    self.update_status("✅ ML Backend is running")
                    time.sleep(2)
                    self.register_backend()
                    return
            except requests.exceptions.RequestException:
                time.sleep(1)
                
        self.update_status("⚠️ Backend failed to start properly")

    def register_backend(self):
        """Register the ML backend with Label Studio"""
        try:
            # Check if Label Studio is running
            if not self.is_label_studio_running():
                self.update_status("⚠️ Label Studio not running. Start it first.")
                return
                
            # Register backend using Label Studio API
            self.register_via_api()
            
        except Exception as e:
            self.update_status(f"⚠️ Backend registration failed: {e}")

    def register_via_api(self):
        """Register backend via Label Studio API"""
        try:
            # Default Label Studio credentials
            login_url = "http://localhost:8080/api/users/login/"
            register_url = "http://localhost:8080/api/ml/"
            
            # Try to register ML backend
            ml_backend_data = {
                "url": "http://localhost:9090",
                "title": "ALF ML Backend",
                "description": "Custom ML backend for ALF"
            }
            
            session = requests.Session()
            
            # Get CSRF token first
            response = session.get("http://localhost:8080/")
            
            # Register ML backend
            response = session.post(register_url, json=ml_backend_data, timeout=10)
            
            if response.status_code in [200, 201]:
                self.backend_registered = True
                self.update_status("✅ Backend registered successfully!")
                # Open Label Studio in browser
                threading.Thread(target=self.open_label_studio_delayed, daemon=True).start()
            else:
                self.update_status(f"⚠️ Registration failed: {response.status_code}")
                
        except Exception as e:
            self.update_status(f"⚠️ API registration failed: {e}")

    def open_label_studio_delayed(self):
        """Open Label Studio in browser after delay"""
        time.sleep(2)
        webbrowser.open("http://localhost:8080")

    def is_label_studio_running(self):
        """Check if Label Studio is running"""
        try:
            response = requests.get("http://localhost:8080", timeout=5)
            return response.status_code == 200
        except:
            return False

    def stop_server_and_exit(self):
        """Stop all processes and exit"""
        if self.server_process:
            try:
                if platform.system() == 'Windows':
                    self.server_process.terminate()
                else:
                    os.kill(self.server_process.pid, signal.SIGTERM)
                self.server_process = None
                self.update_status("🛑 ML Backend stopped")
            except:
                pass
                
        if self.root:
            self.root.destroy()
        sys.exit(0)

    def install_label_studio(self):
        """Install and start Label Studio"""
        self.progress_bar.pack(pady=5)
        self.progress_bar.start(10)
        self.update_status("📦 Installing Label Studio...")

        def task():
            try:
                # Install label-studio
                result = subprocess.run(
                    ["pip", "install", "label-studio"], 
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    # Try with uv if pip fails
                    result = subprocess.run(
                        ["uv", "pip", "install", "label-studio"], 
                        capture_output=True, 
                        text=True,
                        timeout=300
                    )

                if result.returncode == 0:
                    # Start Label Studio
                    self.start_label_studio()
                else:
                    self.root.after(0, self.stop_progress_bar)
                    self.root.after(0, lambda: self.update_status(f"❌ Installation failed: {result.stderr}"))
                    
            except subprocess.TimeoutExpired:
                self.root.after(0, self.stop_progress_bar)
                self.root.after(0, lambda: self.update_status("❌ Installation timed out"))
            except Exception as e:
                self.root.after(0, self.stop_progress_bar)
                self.root.after(0, lambda: self.update_status(f"❌ Installation error: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def start_label_studio(self):
        """Start Label Studio server"""
        try:
            # Start Label Studio in background
            self.label_studio_process = subprocess.Popen(
                ["label-studio", "start", "--port", "8080"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Label Studio to be ready
            threading.Thread(target=self.wait_for_label_studio, daemon=True).start()
            
        except Exception as e:
            self.root.after(0, self.stop_progress_bar)
            self.root.after(0, lambda: self.update_status(f"❌ Failed to start Label Studio: {e}"))

    def wait_for_label_studio(self):
        """Wait for Label Studio to be ready"""
        max_attempts = 60
        for attempt in range(max_attempts):
            if self.is_label_studio_running():
                self.root.after(0, self.stop_progress_bar)
                self.root.after(0, lambda: self.update_status(
                    "✅ Label Studio started! Visit: http://localhost:8080"
                ))
                # Open browser
                threading.Thread(target=self.open_label_studio_delayed, daemon=True).start()
                return
            time.sleep(2)
            
        self.root.after(0, self.stop_progress_bar)
        self.root.after(0, lambda: self.update_status("⚠️ Label Studio took too long to start"))

    def uninstall_label_studio(self):
        """Stop and uninstall Label Studio"""
        self.progress_bar.pack(pady=5)
        self.progress_bar.start(10)
        self.update_status("🛑 Stopping Label Studio...")

        def task():
            try:
                # Stop Label Studio process
                if self.label_studio_process:
                    self.label_studio_process.terminate()
                    self.label_studio_process = None

                # Kill processes on port 8080
                self.kill_processes_on_port(8080)
                
                # Kill processes on port 9090 (ML backend)
                self.kill_processes_on_port(9090)

                # Uninstall package
                try:
                    subprocess.run(["pip", "uninstall", "label-studio", "-y"], 
                                 capture_output=True, text=True)
                except:
                    try:
                        subprocess.run(["uv", "pip", "uninstall", "label-studio", "-y"], 
                                     capture_output=True, text=True)
                    except:
                        pass

                self.root.after(0, self.stop_progress_bar)
                self.root.after(0, lambda: self.update_status("✅ Label Studio stopped and removed!"))

            except Exception as e:
                self.root.after(0, self.stop_progress_bar)
                self.root.after(0, lambda: self.update_status(f"⚠️ Error during cleanup: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def kill_processes_on_port(self, port):
        """Kill processes using specified port"""
        try:
            if platform.system() == 'Windows':
                # Windows
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True
                )
                
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
                # Linux/Mac
                try:
                    subprocess.run(['pkill', '-f', 'label-studio'], capture_output=True)
                    subprocess.run(['pkill', '-f', f':{port}'], capture_output=True)
                except:
                    pass
        except:
            pass

    def stop_progress_bar(self):
        """Stop and hide progress bar"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    def update_status(self, message):
        """Update status label"""
        if self.status_label:
            self.status_label.config(text=message)
        print(message)  # Also print to console

    def run_gui(self):
        """Run the GUI application"""
        self.root = tk.Tk()
        self.root.title("ALF Server Controller")
        self.root.geometry("450x400")
        self.root.resizable(False, False)

        # Title
        title_label = tk.Label(self.root, text="ALF Label Studio Controller", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Instructions
        instructions = tk.Label(self.root, 
                               text="1. Install Label Studio\n2. Start ALF Backend\n3. Use Label Studio with ML Backend", 
                               font=("Arial", 10), 
                               justify="left")
        instructions.pack(pady=5)

        # Buttons
        install_btn = tk.Button(self.root, 
                               text="Step 1: Install & Start Label Studio", 
                               command=self.install_label_studio, 
                               width=40, height=2,
                               bg="#4CAF50", fg="white")
        install_btn.pack(pady=5)

        start_btn = tk.Button(self.root, 
                             text="Step 2: Start ALF ML Backend", 
                             command=self.start_server, 
                             width=40, height=2,
                             bg="#2196F3", fg="white")
        start_btn.pack(pady=5)

        open_btn = tk.Button(self.root, 
                            text="Open Label Studio", 
                            command=lambda: webbrowser.open("http://localhost:8080"), 
                            width=40, height=2,
                            bg="#FF9800", fg="white")
        open_btn.pack(pady=5)

        stop_btn = tk.Button(self.root, 
                            text="Stop ALF & Exit", 
                            command=self.stop_server_and_exit, 
                            width=40, height=2,
                            bg="#f44336", fg="white")
        stop_btn.pack(pady=5)

        uninstall_btn = tk.Button(self.root, 
                                 text="Final: Stop & Uninstall Label Studio", 
                                 command=self.uninstall_label_studio, 
                                 width=40, height=2,
                                 bg="#9E9E9E", fg="white")
        uninstall_btn.pack(pady=5)

        # Progress bar (hidden initially)
        self.progress_bar = ttk.Progressbar(self.root, mode="indeterminate", length=300)

        # Status label at bottom
        self.status_label = tk.Label(self.root, text="Ready to start", 
                                   fg="green", font=("Arial", 10))
        self.status_label.pack(pady=10)

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.stop_server_and_exit)

        self.root.mainloop()


def main():
    """Main entry point"""
    controller = LabelStudioController()
    controller.run_gui()


if __name__ == "__main__":
    main()
