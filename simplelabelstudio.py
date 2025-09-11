"""Simple Label Studio environment manager with Tkinter.

This module provides a very small graphical user interface that lets a user
create a temporary virtual environment for `label-studio` using the `uv`
package manager.  The interface exposes four buttons:

``Create``
    Builds a temporary virtual environment, installs ``label-studio`` and
    starts the web server.  Everything is done inside a directory created by
    :mod:`tempfile` so that it can easily be cleaned up later.

``Check``
    Displays information about the paths being used and whether
    ``label-studio`` appears to be installed correctly.

``Stop``
    Stops the running Label Studio server if it is active.

``Delete``
    Removes the virtual environment directory entirely.

The goal of this file is educational: every function is heavily commented so
that newcomers to Python can follow the logic and experiment.  Real projects
would normally contain more robust error handling, but that would distract
from the core ideas demonstrated here.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------------------
# Global state used by the button callbacks.  In a larger application this
# would likely be managed by a dedicated class, but globals keep the example
# easy to understand.
# ---------------------------------------------------------------------------

# Path to the temporary virtual environment.  ``None`` means no environment has
# been created yet.
env_dir: str | None = None

# Handle to the running Label Studio server process.  ``None`` means the server
# is not currently running.
server_process: subprocess.Popen | None = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def create_env() -> None:
    """Create a temporary virtual environment and install Label Studio.

    The steps performed are:

    1. Use :func:`tempfile.mkdtemp` to create a new, unique directory.
    2. Invoke ``uv venv`` to build a virtual environment inside that directory.
    3. Install the ``label-studio`` package using ``uv pip``.
    4. Start the Label Studio web server and keep a handle to the process so we
       can stop it later.

    This function performs several external commands which are executed using
    :func:`subprocess.run` and :class:`subprocess.Popen`.  These calls may raise
    :class:`subprocess.CalledProcessError` if something goes wrong.
    """

    global env_dir, server_process

    # Avoid creating multiple environments if the user clicks "Create" twice.
    if env_dir is not None:
        messagebox.showinfo("Environment", f"Environment already exists at {env_dir}")
        return

    # 1. Create the temporary directory.
    env_dir = tempfile.mkdtemp(prefix="labelstudio-")

    # 2. Create the virtual environment using ``uv``.  ``check=True`` ensures an
    #    exception is raised if the command fails.
    subprocess.run(["uv", "venv", env_dir], check=True)

    # 3. Install the ``label-studio`` package inside the new environment.  The
    #    ``cwd`` argument changes the working directory so that ``uv`` operates
    #    on the freshly created environment.
    subprocess.run(["uv", "pip", "install", "label-studio"], check=True, cwd=env_dir)

    # 4. Start the Label Studio server.  The executable lives in the ``bin``
    #    directory of the virtual environment.  ``Popen`` is used here instead
    #    of ``run`` because we want the server to run in the background.
    executable = os.path.join(env_dir, "bin", "label-studio")
    server_process = subprocess.Popen([executable, "start"], cwd=env_dir)

    messagebox.showinfo("Environment", f"Environment created in\n{env_dir}")


def check_env() -> str:
    """Return information about the current setup.

    The function checks:

    * The location of the ``uv`` command using :func:`shutil.which`.
    * Whether a virtual environment has been created.
    * Whether ``label-studio`` appears to be installed in that environment.

    The resulting information is both returned and displayed in a message box
    for convenience.
    """

    uv_path = shutil.which("uv")

    # Determine if Label Studio is installed by asking the virtual environment
    # Python to report the package version.  Any failure is interpreted as the
    # package being missing.
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
            ls_installed = False

    info = (
        f"uv executable: {uv_path}\n"
        f"env dir: {env_dir}\n"
        f"label-studio installed: {ls_installed}"
    )

    messagebox.showinfo("Environment", info)
    return info


def stop_server() -> None:
    """Terminate the running Label Studio server, if any."""

    global server_process

    if server_process is not None:
        server_process.terminate()
        server_process = None
        messagebox.showinfo("Environment", "Server stopped")


def delete_env() -> None:
    """Remove the temporary virtual environment entirely."""

    global env_dir

    # Ensure the server is not running while we delete its files.
    stop_server()

    if env_dir is not None:
        shutil.rmtree(env_dir)
        messagebox.showinfo("Environment", f"Deleted environment at\n{env_dir}")
        env_dir = None


# ---------------------------------------------------------------------------
# Tkinter user interface
# ---------------------------------------------------------------------------

def main() -> None:
    """Launch the graphical user interface."""

    root = tk.Tk()
    root.title("Simple Label Studio")

    # Using ``threading.Thread`` for the create button prevents the UI from
    # freezing while ``uv`` performs potentially long operations.
    tk.Button(root, text="Create", command=lambda: threading.Thread(target=create_env).start()).pack(
        fill=tk.X
    )
    tk.Button(root, text="Check", command=check_env).pack(fill=tk.X)
    tk.Button(root, text="Stop", command=stop_server).pack(fill=tk.X)
    tk.Button(root, text="Delete", command=delete_env).pack(fill=tk.X)

    root.mainloop()


if __name__ == "__main__":
    main()
