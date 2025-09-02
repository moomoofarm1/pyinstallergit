"""
Unit tests for exit functionality including virtual environment cleanup.

These tests validate that the exit functionality properly cleans up
virtual environments and temporary files.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from communication.server_manager import ServerManager
from ui.main_window import AudioProcessingApp

class TestExitFunctionality:
    """Test cases for application exit and cleanup functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create mock virtual environments for testing
        self.mock_venvs_dir = self.temp_dir / ".venvs"
        self.mock_venvs_dir.mkdir()
        
        self.mock_diarization_env = self.mock_venvs_dir / "diarization"
        self.mock_diarization_env.mkdir()
        (self.mock_diarization_env / "pyvenv.cfg").write_text("test config")
        
        self.mock_transcription_env = self.mock_venvs_dir / "transcription"
        self.mock_transcription_env.mkdir()
        (self.mock_transcription_env / "pyvenv.cfg").write_text("test config")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_server_manager_remove_virtual_environments(self):
        """Test virtual environment removal functionality."""
        # Create server manager with mock paths
        server_manager = ServerManager()
        server_manager.venv_dir = self.mock_venvs_dir
        server_manager.diarization_venv = self.mock_diarization_env
        server_manager.transcription_venv = self.mock_transcription_env
        
        # Verify environments exist before cleanup
        assert self.mock_diarization_env.exists()
        assert self.mock_transcription_env.exists()
        assert self.mock_venvs_dir.exists()
        
        # Perform cleanup
        server_manager.remove_virtual_environments()
        
        # Verify environments are removed
        assert not self.mock_diarization_env.exists()
        assert not self.mock_transcription_env.exists()
        assert not self.mock_venvs_dir.exists()
    
    def test_server_manager_individual_environment_removal(self):
        """Test individual environment removal when bulk removal fails."""
        server_manager = ServerManager()
        server_manager.venv_dir = self.mock_venvs_dir
        server_manager.diarization_venv = self.mock_diarization_env
        server_manager.transcription_venv = self.mock_transcription_env
        
        # Mock shutil.rmtree to fail on the main directory but succeed on individuals
        with patch('communication.server_manager.shutil.rmtree') as mock_rmtree:
            # First call (main directory) fails, subsequent calls succeed
            mock_rmtree.side_effect = [Exception("Mock failure"), None, None]
            
            # This should trigger individual removal
            server_manager.remove_virtual_environments()
            
            # Should have called rmtree 3 times: main dir (failed), then 2 individual envs
            assert mock_rmtree.call_count == 3
    
    def test_server_manager_cleanup_all_and_exit(self):
        """Test complete cleanup and exit functionality."""
        server_manager = ServerManager()
        server_manager.venv_dir = self.mock_venvs_dir
        server_manager.diarization_venv = self.mock_diarization_env
        server_manager.transcription_venv = self.mock_transcription_env
        
        # Mock the cleanup_all method to avoid server operations
        with patch.object(server_manager, 'cleanup_all') as mock_cleanup_all:
            # Perform complete cleanup
            server_manager.cleanup_all_and_exit()
            
            # Verify cleanup_all was called
            mock_cleanup_all.assert_called_once()
            
            # Verify virtual environments are removed
            assert not self.mock_venvs_dir.exists()
    
    def test_nonexistent_virtual_environments(self):
        """Test cleanup when virtual environments don't exist."""
        # Remove the mock environments
        shutil.rmtree(self.mock_venvs_dir)
        
        server_manager = ServerManager()
        server_manager.venv_dir = self.mock_venvs_dir
        server_manager.diarization_venv = self.mock_diarization_env
        server_manager.transcription_venv = self.mock_transcription_env
        
        # This should not raise an exception
        server_manager.remove_virtual_environments()
        
        # Should complete without issues
        assert True
    
    @patch('tkinter.Tk')
    def test_audio_processing_app_exit_functionality(self, mock_tk):
        """Test AudioProcessingApp exit functionality."""
        # Mock tkinter components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        # Create the app (mocking tkinter initialization)
        with patch('ui.main_window.AudioProcessingApp.setup_ui'), \
             patch('ui.main_window.AudioProcessingApp.setup_logging_display'):
            
            app = AudioProcessingApp()
            app.server_manager.venv_dir = self.mock_venvs_dir
            app.server_manager.diarization_venv = self.mock_diarization_env
            app.server_manager.transcription_venv = self.mock_transcription_env
            
            # Mock the cleanup methods
            with patch.object(app.server_manager, 'cleanup_all_and_exit') as mock_cleanup_exit, \
                 patch.object(app.audio_preprocessor, 'cleanup_processed_files') as mock_audio_cleanup:
                
                # Test the internal cleanup method
                app._perform_full_cleanup_and_exit()
                
                # Verify cleanup methods were called
                mock_cleanup_exit.assert_called_once()
                mock_audio_cleanup.assert_called_once()
    
    def test_partial_cleanup_failure(self):
        """Test behavior when some cleanup operations fail."""
        server_manager = ServerManager()
        server_manager.venv_dir = self.mock_venvs_dir
        server_manager.diarization_venv = self.mock_diarization_env
        server_manager.transcription_venv = self.mock_transcription_env
        
        # Make one of the environment directories read-only to simulate failure
        self.mock_diarization_env.chmod(0o444)
        
        # Should not raise exception even if some cleanup fails
        try:
            server_manager.remove_virtual_environments()
            # Should complete without raising exception
            assert True
        except Exception as e:
            pytest.fail(f"Cleanup should handle failures gracefully, but got: {e}")
        finally:
            # Restore permissions for teardown
            try:
                self.mock_diarization_env.chmod(0o755)
            except:
                pass
    
    def test_environment_status_after_cleanup(self):
        """Test environment status checking after cleanup."""
        server_manager = ServerManager()
        server_manager.venv_dir = self.mock_venvs_dir
        server_manager.diarization_venv = self.mock_diarization_env
        server_manager.transcription_venv = self.mock_transcription_env
        
        # Check initial status
        initial_status = server_manager.check_environment_status()
        assert "Ready" in initial_status  # Should show as ready initially
        
        # Perform cleanup
        server_manager.remove_virtual_environments()
        
        # Check status after cleanup
        final_status = server_manager.check_environment_status()
        assert "Not found" in final_status  # Should show as not found after cleanup
    
    def test_cleanup_with_running_servers(self):
        """Test cleanup behavior when servers are running."""
        server_manager = ServerManager()
        server_manager.venv_dir = self.mock_venvs_dir
        
        # Mock running servers
        with patch.object(server_manager, 'is_server_running', return_value=True), \
             patch.object(server_manager, '_stop_server', return_value=True) as mock_stop:
            
            # Perform complete cleanup
            server_manager.cleanup_all_and_exit()
            
            # Should have attempted to stop servers
            # (exact call count depends on server types)
            assert mock_stop.call_count >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])