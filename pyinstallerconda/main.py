#!/usr/bin/env python3
"""
PyInstaller Label Studio Launcher
Starts Label Studio frontend and ML backend as subprocesses
"""

import subprocess
import sys
import time
import os
import signal
import atexit
import threading
from pathlib import Path


class LabelStudioLauncher:
    def __init__(self):
        self.frontend_process = None
        self.backend_process = None
        self.processes = []

    def cleanup(self):
        """Clean up all spawned processes"""
        print("Cleaning up processes...")
        for process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:  # Still running, force kill
                        process.kill()
            except Exception as e:
                print(f"Error cleaning up process: {e}")

    def start_frontend(self):
        """Start Label Studio frontend"""
        try:
            print("Starting Label Studio frontend...")
            cmd = [sys.executable, "-m", "label_studio.server"]
            self.frontend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(self.frontend_process)
            print(f"Frontend started with PID: {self.frontend_process.pid}")
            return True
        except Exception as e:
            print(f"Failed to start frontend: {e}")
            return False

    def start_backend(self):
        """Start Label Studio ML backend"""
        try:
            print("Starting Label Studio ML backend...")
            cmd = [sys.executable, "-m", "label_studio_ml.server"]
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(self.backend_process)
            print(f"Backend started with PID: {self.backend_process.pid}")
            return True
        except Exception as e:
            print(f"Failed to start backend: {e}")
            return False

    def monitor_processes(self):
        """Monitor processes and restart if needed"""
        while True:
            try:
                # Check frontend
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("Frontend process died, restarting...")
                    self.start_frontend()

                # Check backend
                if self.backend_process and self.backend_process.poll() is not None:
                    print("Backend process died, restarting...")
                    self.start_backend()

                time.sleep(5)  # Check every 5 seconds

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in process monitoring: {e}")
                time.sleep(5)

    def run(self):
        """Main execution function"""
        # Register cleanup function
        atexit.register(self.cleanup)

        # Handle signals
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup() or sys.exit(0))
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup() or sys.exit(0))

        print("PyInstaller Label Studio Launcher")
        print("=" * 40)

        # Start services
        if not self.start_backend():
            print("Failed to start ML backend. Exiting.")
            sys.exit(1)

        # Wait a moment for backend to initialize
        time.sleep(3)

        if not self.start_frontend():
            print("Failed to start frontend. Exiting.")
            sys.exit(1)

        print("\nLabel Studio is starting up...")
        print("Frontend will be available at: http://localhost:8080")
        print("ML Backend will be available at: http://localhost:9090")
        print("\nPress Ctrl+C to stop all services")

        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()

        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutdown requested...")
            self.cleanup()
            sys.exit(0)


def main():
    launcher = LabelStudioLauncher()
    launcher.run()


if __name__ == "__main__":
    main()