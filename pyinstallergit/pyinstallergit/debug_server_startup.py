#!/usr/bin/env python3
"""
Debug script to isolate the diarization server startup issue.
This script will help identify exactly where the include_label_studio error is coming from.
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]',
    handlers=[
        logging.FileHandler('debug_server_startup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_method_signatures():
    """Test the actual method signatures in the loaded modules."""
    logger.info("=== TESTING METHOD SIGNATURES ===")
    
    try:
        from communication.server_manager import ServerManager
        import inspect
        
        # Check the actual method signature
        sig = inspect.signature(ServerManager._setup_diarization_environment)
        logger.info(f"_setup_diarization_environment signature: {sig}")
        
        # Check if there are any other methods with similar names
        methods = [method for method in dir(ServerManager) if 'setup' in method.lower()]
        logger.info(f"Methods containing 'setup': {methods}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to test method signatures: {e}")
        logger.error(traceback.format_exc())
        return False

def test_server_manager_creation():
    """Test ServerManager creation and initialization."""
    logger.info("=== TESTING SERVER MANAGER CREATION ===")
    
    try:
        from communication.server_manager import ServerManager
        sm = ServerManager()
        logger.info("ServerManager created successfully")
        
        # Test basic properties
        logger.info(f"Virtual environment directory: {sm.venv_dir}")
        logger.info(f"Diarization venv path: {sm.diarization_venv}")
        
        return sm
        
    except Exception as e:
        logger.error(f"Failed to create ServerManager: {e}")
        logger.error(traceback.format_exc())
        return None

def test_diarization_startup_isolated():
    """Test just the diarization environment setup in isolation."""
    logger.info("=== TESTING DIARIZATION ENVIRONMENT SETUP (ISOLATED) ===")
    
    try:
        from communication.server_manager import ServerManager
        sm = ServerManager()
        
        # Clear any existing environment
        import shutil
        if sm.diarization_venv.exists():
            logger.info(f"Removing existing diarization environment: {sm.diarization_venv}")
            shutil.rmtree(str(sm.diarization_venv))
        
        # Test the setup method directly
        logger.info("Calling _setup_diarization_environment() directly...")
        sm._setup_diarization_environment()
        logger.info("_setup_diarization_environment() completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Diarization environment setup failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_start_server_method():
    """Test the _start_server method for DIARIZATION type."""
    logger.info("=== TESTING _start_server METHOD ===")
    
    try:
        from communication.server_manager import ServerManager, ServerType
        sm = ServerManager()
        
        # Test the method that actually gets called
        logger.info("Attempting to call _start_server(ServerType.DIARIZATION)...")
        result = sm._start_server(ServerType.DIARIZATION)
        logger.info(f"_start_server returned: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"_start_server failed: {e}")
        logger.error(traceback.format_exc())
        
        # Log the exact error details
        if "include_label_studio" in str(e):
            logger.error("FOUND THE ERROR SOURCE: include_label_studio parameter issue")
            logger.error("Full traceback:")
            for line in traceback.format_tb(e.__traceback__):
                logger.error(line.strip())
        
        return False

def test_ui_integration():
    """Test the UI call path that triggers the error."""
    logger.info("=== TESTING UI INTEGRATION ===")
    
    try:
        from communication.server_manager import ServerManager
        sm = ServerManager()
        
        # This mimics what the UI does
        logger.info("Calling start_diarization_server(with_label_studio=True)...")
        result = sm.start_diarization_server(with_label_studio=True)
        logger.info(f"start_diarization_server returned: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"UI integration test failed: {e}")
        logger.error(traceback.format_exc())
        
        # Analyze the exact call stack
        logger.error("=== CALL STACK ANALYSIS ===")
        for frame_info in traceback.extract_tb(e.__traceback__):
            logger.error(f"File: {frame_info.filename}:{frame_info.lineno}")
            logger.error(f"Function: {frame_info.name}")
            logger.error(f"Code: {frame_info.line}")
            logger.error("---")
        
        return False

def main():
    """Run all debugging tests."""
    logger.info("Starting comprehensive debugging of diarization server startup...")
    
    # Test 1: Method signatures
    if not test_method_signatures():
        logger.error("Method signature test failed - stopping")
        return
    
    # Test 2: ServerManager creation
    sm = test_server_manager_creation()
    if sm is None:
        logger.error("ServerManager creation failed - stopping")
        return
    
    # Test 3: Isolated environment setup
    if not test_diarization_startup_isolated():
        logger.error("Isolated environment setup failed - but continuing...")
    
    # Test 4: _start_server method
    if not test_start_server_method():
        logger.error("_start_server method failed - this might be where the error occurs")
    
    # Test 5: Full UI integration
    if not test_ui_integration():
        logger.error("UI integration test failed - this simulates the actual user action")
    
    logger.info("Debugging completed. Check debug_server_startup.log for detailed output.")

if __name__ == "__main__":
    main()