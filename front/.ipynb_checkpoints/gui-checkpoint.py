import tkinter as tk
import subprocess
import os
import signal
import sys

server_process = None  # Will store the subprocess.Popen object

def start_server():
    global server_process
    if server_process is None:
        # Start FastAPI server in a subprocess
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9090"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        status_label.config(text="Server running...", fg="green")
    else:
        status_label.config(text="Server is already running", fg="orange")

def stop_server():
    global server_process
    if server_process is not None:
        # Send termination signal
        os.kill(server_process.pid, signal.SIGTERM)
        server_process = None
        status_label.config(text="Server stopped.", fg="red")
        root.after(500, root.destroy)  # Close Tkinter window
        sys.exit(0)  # Terminate Python runtime
    else:
        status_label.config(text="Server is not running", fg="orange")

# Create GUI
root = tk.Tk()
root.title("FastAPI Server Controller")

start_btn = tk.Button(root, text="Start Server", command=start_server, bg="lightgreen", width=20)
start_btn.pack(pady=10)

stop_btn = tk.Button(root, text="Stop Server & Exit", command=stop_server, bg="lightcoral", width=20)
stop_btn.pack(pady=10)

status_label = tk.Label(root, text="Server not running", fg="red")
status_label.pack(pady=10)

root.mainloop()
