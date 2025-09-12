"""
ALF - Advanced Audio Label Frontend

Main entry point for the audio processing pipeline application.
This application provides a unified interface for audio diarization and transcription
workflows using Label Studio frontend and specialized ML backends.

Features:
- Audio preprocessing (MP3 to 16KHz mono conversion)
- Speaker diarization using pyannote.audio
- Speech transcription using NeMo ASR
- Browser-Server architecture with JSON communication
- Separate virtual environments for different pipelines

Author: ALF Development Team
Version: 0.2.0
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path to ensure module imports work correctly
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alf.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the ALF application.
    
    This function initializes and starts the tkinter-based user interface
    which allows users to control the audio processing pipelines.
    """
    try:
        # Import the UI module (only after path is set up)
        from ui.main_window import AudioProcessingApp
        
        logger.info("Starting ALF - Advanced Audio Label Frontend")
        
        # Initialize and run the main application window
        app = AudioProcessingApp()
        app.run()
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Please ensure all dependencies are installed using 'uv sync'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during application startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
