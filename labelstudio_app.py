#!/usr/bin/env python3
"""
Clean Label Studio Application with ML Backend
Minimal implementation with Label Studio + Label Studio ML + PyInstaller
"""

import os
import sys
import time
import threading
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('labelstudio_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LabelStudioMLBackend:
    """Simple Label Studio ML Backend"""

    def __init__(self, port: int = 9090):
        self.port = port
        self.temp_dir = Path(tempfile.mkdtemp(prefix="labelstudio_ml_"))
        self.process: Optional[subprocess.Popen] = None

    def create_ml_backend_script(self) -> Path:
        """Create a simple ML backend script"""
        script_content = '''
import os
import json
from label_studio_ml.model import LabelStudioMLBase

class SimpleMLBackend(LabelStudioMLBase):
    """Simple ML Backend for Label Studio"""

    def __init__(self, **kwargs):
        super(SimpleMLBackend, self).__init__(**kwargs)
        print("Simple ML Backend initialized")

    def predict(self, tasks, **kwargs):
        """Simple prediction function - returns empty predictions"""
        predictions = []

        for task in tasks:
            # Return empty predictions for now
            # Users can customize this method for their specific ML needs
            predictions.append({
                "result": [],
                "score": 0.0
            })

        return predictions

    def fit(self, completions, workdir=None, **kwargs):
        """Training function - not implemented"""
        return {"status": "ok", "message": "Training not implemented"}

if __name__ == "__main__":
    import argparse
    from label_studio_ml.server import init_app

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9090, help="ML backend port")
    parser.add_argument("--host", type=str, default="localhost", help="ML backend host")
    args = parser.parse_args()

    # Create the ML backend app
    app = init_app(
        model_class=SimpleMLBackend,
        model_dir=os.path.dirname(__file__),
        redis_queue=False,
        redis_host=None,
        redis_port=None
    )

    # Run the server
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
'''

        script_path = self.temp_dir / "ml_backend.py"
        with open(script_path, 'w') as f:
            f.write(script_content)

        return script_path

    def start_ml_backend(self) -> bool:
        """Start the ML backend server"""
        try:
            script_path = self.create_ml_backend_script()

            # Start ML backend process
            self.process = subprocess.Popen([
                sys.executable, str(script_path),
                "--port", str(self.port),
                "--host", "localhost"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            logger.info(f"ML backend started on port {self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start ML backend: {e}")
            return False

    def stop_ml_backend(self):
        """Stop the ML backend server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("ML backend stopped")

    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


class LabelStudioFrontend:
    """Label Studio Frontend Server Manager"""

    def __init__(self, port: int = 8080, project_name: str = "LabelStudio"):
        self.port = port
        self.project_name = project_name
        self.process: Optional[subprocess.Popen] = None
        self.data_dir = Path("label_studio_data")
        self.data_dir.mkdir(exist_ok=True)

    def start_frontend(self) -> bool:
        """Start Label Studio frontend server"""
        try:
            # Set environment variables
            env = os.environ.copy()
            env["LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED"] = "true"
            env["LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT"] = str(Path.cwd())

            # Start Label Studio frontend
            cmd = [
                "label-studio", "start",
                f"--port={self.port}",
                f"--data-dir={self.data_dir}",
                "--log-level=INFO"
            ]

            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            logger.info(f"Label Studio frontend started on port {self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start Label Studio frontend: {e}")
            return False

    def stop_frontend(self):
        """Stop the Label Studio frontend"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("Label Studio frontend stopped")


class LabelStudioApp:
    """Main Label Studio application with ML backend"""

    def __init__(self):
        self.frontend = LabelStudioFrontend(port=8080)
        self.ml_backend = LabelStudioMLBackend(port=9090)
        self.frontend_thread: Optional[threading.Thread] = None
        self.backend_thread: Optional[threading.Thread] = None
        self.running = False

    def start_services(self):
        """Start both frontend and ML backend services"""
        logger.info("Starting Label Studio Application...")

        # Start ML backend in thread
        self.backend_thread = threading.Thread(
            target=self._start_ml_backend_thread,
            daemon=True
        )
        self.backend_thread.start()

        # Wait for backend to start
        time.sleep(3)

        # Start frontend in thread
        self.frontend_thread = threading.Thread(
            target=self._start_frontend_thread,
            daemon=True
        )
        self.frontend_thread.start()

        # Wait for frontend to start
        time.sleep(5)

        self.running = True
        logger.info("All services started successfully!")
        logger.info(f"Label Studio UI: http://localhost:8080")
        logger.info(f"ML Backend: http://localhost:9090")

    def _start_ml_backend_thread(self):
        """Thread function for ML backend"""
        self.ml_backend.start_ml_backend()

    def _start_frontend_thread(self):
        """Thread function for frontend"""
        self.frontend.start_frontend()

    def stop_services(self):
        """Stop all services"""
        logger.info("Stopping all services...")
        self.running = False

        if self.frontend:
            self.frontend.stop_frontend()

        if self.ml_backend:
            self.ml_backend.stop_ml_backend()
            self.ml_backend.cleanup()

        logger.info("All services stopped")

    def run(self):
        """Main application loop"""
        try:
            self.start_services()

            print("\n" + "="*60)
            print("LABEL STUDIO APPLICATION RUNNING")
            print("="*60)
            print("Label Studio UI: http://localhost:8080")
            print("ML Backend API: http://localhost:9090")
            print("\nInstructions:")
            print("1. Open http://localhost:8080 in your browser")
            print("2. Create a new project for data labeling")
            print("3. Configure ML backend URL: http://localhost:9090")
            print("4. Upload data files for labeling")
            print("5. Press Ctrl+C to stop the application")
            print("="*60)

            # Keep main thread alive
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.stop_services()


def main():
    """Main entry point"""
    print("Label Studio Application with ML Backend")
    print("Clean implementation for PyInstaller packaging")

    app = LabelStudioApp()
    app.run()


if __name__ == "__main__":
    main()