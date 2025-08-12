import tkinter as tk
import threading
import subprocess
import sys
import os
import signal
import webbrowser
import time

server_process = None

def start_server():
    global server_process
    if server_process is None:
        # Start server in a background process
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9090"]
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

def run_gui():
    global root
    root = tk.Tk()
    root.title("FastAPI Server Controller")
    root.geometry("300x150")

    start_btn = tk.Button(root, text="Start Server", command=start_server, width=20, height=2)
    start_btn.pack(pady=10)

    stop_btn = tk.Button(root, text="Stop Server & Exit", command=stop_server_and_exit, width=20, height=2)
    stop_btn.pack(pady=10)

    root.mainloop()
