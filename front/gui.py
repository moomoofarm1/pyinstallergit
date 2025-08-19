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

def install_label_studio():
    threading.Thread(
        target=lambda: subprocess.call([sys.executable, "-m", "pip", "install", "label-studio"]),
        daemon=True
    ).start()

def uninstall_label_studio():
    threading.Thread(
        target=lambda: subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", "label-studio"]),
        daemon=True
    ).start()

def run_gui():
    global root
    root = tk.Tk()
    root.title("ALF Server Controller")
    root.geometry("300x250")

    start_btn = tk.Button(root, text="Start ALF", command=start_server, width=25, height=2)
    start_btn.pack(pady=5)

    stop_btn = tk.Button(root, text="Stop ALF & Exit", command=stop_server_and_exit, width=25, height=2)
    stop_btn.pack(pady=5)

    install_btn = tk.Button(root, text="Step 1. Install label-studio", command=install_label_studio, width=25, height=2)
    install_btn.pack(pady=5)

    uninstall_btn = tk.Button(root, text="Final step. Uninstall label-studio", command=uninstall_label_studio, width=25, height=2)
    uninstall_btn.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
