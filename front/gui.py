import tkinter as tk
import threading
import subprocess
import sys
import os
import signal

# Store process handle so we can stop it
server_process = None

def start_server():
    global server_process
    if server_process is None:
        # Run uvicorn as a subprocess
        # --reload is optional; remove in production
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9090"]
        )

def stop_server_and_exit():
    global server_process
    if server_process:
        # Send SIGTERM to uvicorn
        if os.name == 'nt':  # Windows
            server_process.terminate()
        else:  # Unix/Mac
            os.kill(server_process.pid, signal.SIGTERM)
        server_process = None

    # Close the entire Python runtime
    root.destroy()
    sys.exit(0)

def run_gui():
    global root
    root = tk.Tk()
    root.title("ALF Server Controller")
    root.geometry("300x150")

    start_btn = tk.Button(root, text="Start Server", command=start_server, width=20, height=2)
    start_btn.pack(pady=10)

    stop_btn = tk.Button(root, text="Stop Server & Exit", command=stop_server_and_exit, width=20, height=2)
    stop_btn.pack(pady=10)

    root.mainloop()
