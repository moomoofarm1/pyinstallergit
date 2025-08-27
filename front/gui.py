import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import sys, os
import signal
import webbrowser
import time
import shutil
from pathlib import Path
import platform

server_process = None
progress_bar = None
status_label = None

def start_server():
    global server_process
    if server_process is None:
        env = os.environ.copy()
        env["HF_TOKEN"] = os.getenv("HF_TOKEN", "")  # Read from environment or empty
        # Start server in a background process using uvicorn directly
        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "server:app",
                "--host",
                "0.0.0.0",
                "--port",
                "9090",
                "--reload"
            ],
            env=env
        )
        # Give it a short delay to start up, then open in browser
        threading.Thread(target=open_browser_delayed, daemon=True).start()

def open_browser_delayed():
    time.sleep(2)  # wait for server to boot
    webbrowser.open("http://127.0.0.1:9090")

def stop_server_and_exit():
    global server_process
    if server_process:
        if os.name == 'nt':  # Windows
            server_process.terminate()
        else:
            os.kill(server_process.pid, signal.SIGTERM)
        server_process = None
    root.destroy()
    sys.exit(0)

def install_label_studio():
    progress_bar.pack(pady=5)
    progress_bar.start(10)

    def task():
        # Install label-studio
        result = subprocess.run(
            ["pip", "install", "label-studio"], capture_output=True, text=True
        )

        if result.returncode != 0:
            msg = f"Installation failed: {result.stderr}"
        else:
            # Start Label Studio after install
            try:
                subprocess.Popen(["label-studio", "start"])
                msg = 'label-studio successfully installed and started! Use browser and enter: http://localhost:8080/user/login/'
            except Exception as e:
                msg = f"Installed, but failed to start: {e}"

        root.after(0, stop_progress_bar)
        root.after(0, lambda: update_status(msg))

    threading.Thread(target=task, daemon=True).start()

def uninstall_label_studio():
    progress_bar.pack(pady=5)
    progress_bar.start(10)

    def task():
        try:
            # Cross-platform process termination
            if os.name == 'nt':  # Windows
                # Find what's using port 8080
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if ':8080' in line and 'LISTENING' in line:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            print(f"Process {pid} is using port 8080")
                            subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                            print(f"Killed process {pid}")
            else:  # Linux/Mac
                subprocess.run(['pkill', '-9', '-f', 'label-studio'], capture_output=True)
        except Exception as e:
            print(f"Error stopping processes: {e}")

        # Uninstall package
        try:
            subprocess.call(["pip", "uninstall", "label-studio", "-y"])
        except Exception as e:
            print(f"Error uninstalling: {e}")

        root.after(0, stop_progress_bar)
        root.after(0, lambda: update_status("label-studio successfully stopped and removed!"))

    threading.Thread(target=task, daemon=True).start()

def stop_progress_bar():
    progress_bar.stop()
    progress_bar.pack_forget()

def update_status(message):
    status_label.config(text=message)

def run_gui():
    global root, progress_bar, status_label
    root = tk.Tk()
    root.title("ALF Server Controller")
    root.geometry("400x350")

    start_btn = tk.Button(root, text="Start ALF", command=start_server, width=30, height=2)
    start_btn.pack(pady=5)

    stop_btn = tk.Button(root, text="Stop ALF & Exit", command=stop_server_and_exit, width=30, height=2)
    stop_btn.pack(pady=5)

    install_btn = tk.Button(root, text="Step 1. Install and start label-studio", command=install_label_studio, width=30, height=2)
    install_btn.pack(pady=5)

    uninstall_btn = tk.Button(root, text="Final step. stop and uninstall label-studio", command=uninstall_label_studio, width=30, height=2)
    uninstall_btn.pack(pady=5)

    # Progress bar (hidden initially)
    progress_bar = ttk.Progressbar(root, mode="indeterminate", length=250)

    # Status label at bottom
    status_label = tk.Label(root, text="Ready to start. First install Label Studio, then start ALF.", fg="blue")
    status_label.pack(pady=10)

    root.mainloop()
