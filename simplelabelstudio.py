"""Minimal Tkinter helper to run Label Studio in a temporary environment."""

import os
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox

# Paths to the temporary virtual environment and running server process
env_dir = None
server_process = None

def start_env():
    """Create a temp env, install label-studio and launch the server."""
    global env_dir, server_process
    if env_dir is not None:
        messagebox.showinfo("Environment", f"Environment already exists at {env_dir}")
        return
    env_dir = tempfile.mkdtemp(prefix="labelstudio-")
    subprocess.run(["uv", "venv", env_dir], check=True)
    subprocess.run(["uv", "pip", "install", "label-studio"], check=True, cwd=env_dir)
    exe = os.path.join(env_dir, "bin", "label-studio")
    server_process = subprocess.Popen([exe, "start"], cwd=env_dir)
    messagebox.showinfo("Environment", f"Environment created in\n{env_dir}")

def check_env():
    """Show env path and whether label-studio responds."""
    ls_installed = False
    if env_dir is not None:
        python_path = os.path.join(env_dir, "bin", "python")
        try:
            subprocess.run(
                [python_path, "-m", "label_studio", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            ls_installed = True
        except subprocess.CalledProcessError:
            pass
    info = f"env dir: {env_dir}\nlabel-studio installed: {ls_installed}"
    messagebox.showinfo("Environment", info)
    return info

def stop_env():
    """Terminate server and remove the temporary environment."""
    global env_dir, server_process
    if server_process is not None:
        server_process.terminate()
        server_process = None
    if env_dir is not None:
        shutil.rmtree(env_dir)
        messagebox.showinfo("Environment", f"Deleted environment at\n{env_dir}")
        env_dir = None

def main():
    """Launch the minimal graphical interface."""
    root = tk.Tk()
    root.title("Simple Label Studio")
    tk.Button(root, text="Start", command=lambda: threading.Thread(target=start_env).start()).pack(fill=tk.X)
    tk.Button(root, text="Check", command=check_env).pack(fill=tk.X)
    tk.Button(root, text="Stop", command=stop_env).pack(fill=tk.X)
    root.mainloop()

if __name__ == "__main__":  # pragma: no cover - manual use only
    main()
