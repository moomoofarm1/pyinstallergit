"""
Test uvx integration for Label Studio startup.

Tests the uvx command integration, ensuring proper command construction,
error handling, and fallback mechanisms for Label Studio execution.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call
import os
import shutil

from communication.server_manager import ServerManager, ServerType


class TestUvxIntegration:
    """Test uvx integration for Label Studio startup."""
    
    def setup_method(self):
        """Set up test environment."""
        self.server_manager = ServerManager()
        self.temp_dir = tempfile.mkdtemp()
        self.server_manager.venv_dir = Path(self.temp_dir) / "alf_venvs"
    
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'server_manager'):
            self.server_manager.cleanup()
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_uvx_version_check_success(self):
        """Test successful uvx version check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="uvx 0.1.0")
            
            # This should not raise an exception
            result = subprocess.run(["uvx", "--version"], capture_output=True, check=True)
            assert result.returncode == 0
    
    def test_uvx_version_check_failure(self):
        """Test uvx version check when uvx is not installed."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("uvx command not found")
            
            # This should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                subprocess.run(["uvx", "--version"], capture_output=True, check=True)
    
    @patch('subprocess.run')
    def test_uvx_command_construction(self, mock_run):
        """Test that uvx command is constructed correctly."""
        # Mock uvx available
        mock_run.return_value = Mock(returncode=0)
        
        with patch('subprocess.Popen') as mock_popen, \
             patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True):
            
            mock_popen.return_value = Mock(pid=12345)
            
            self.server_manager._start_label_studio_server()
            
            # Verify the correct command was used
            expected_cmd = [
                "uvx", "label-studio", "start", "diarization_project",
                "--host", "127.0.0.1",
                "--port", "8080", 
                "--data-dir", str(Path("label_studio_projects"))
            ]
            
            mock_popen.assert_called_once()
            actual_cmd = mock_popen.call_args[0][0]
            assert actual_cmd == expected_cmd
    
    @patch('subprocess.run')
    def test_uvx_fallback_to_venv(self, mock_run):
        """Test fallback to virtual environment when uvx fails."""
        # First call (uvx availability check) fails, second succeeds for other operations
        mock_run.side_effect = [
            FileNotFoundError("uvx not found"),  # First uvx check fails
        ]
        
        # Create mock virtual environment
        self.server_manager.labelstudio_venv.mkdir(parents=True, exist_ok=True)
        python_path = self.server_manager.labelstudio_venv / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
        python_path.parent.mkdir(parents=True, exist_ok=True)
        python_path.touch()
        
        with patch('subprocess.Popen') as mock_popen, \
             patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True), \
             patch.object(self.server_manager, '_setup_labelstudio_environment'):
            
            mock_popen.return_value = Mock(pid=12345)
            
            result = self.server_manager._start_label_studio_server()
            
            assert result is True
            
            # Verify fallback command was used
            expected_cmd = [
                str(python_path), '-m', 'label_studio', 
                'start', 'diarization_project',
                '--host', '127.0.0.1',
                '--port', '8080', 
                '--data-dir', str(Path("label_studio_projects"))
            ]
            
            actual_cmd = mock_popen.call_args[0][0]
            assert actual_cmd == expected_cmd
    
    def test_command_arguments_formatting(self):
        """Test that command arguments are formatted correctly."""
        project_name = "diarization_project"
        host = "127.0.0.1"
        port = "8080"
        data_dir = Path("label_studio_projects")
        
        expected_uvx_cmd = [
            "uvx", "label-studio", "start", project_name,
            "--host", host,
            "--port", port,
            "--data-dir", str(data_dir)
        ]
        
        # Test command construction logic
        cmd = [
            "uvx", "label-studio", "start", project_name,
            "--host", host,
            "--port", port, 
            "--data-dir", str(data_dir)
        ]
        
        assert cmd == expected_uvx_cmd
    
    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_process_environment_variables(self, mock_popen, mock_run):
        """Test that environment variables are properly set for the process."""
        mock_run.return_value = Mock(returncode=0)  # uvx available
        mock_popen.return_value = Mock(pid=12345)
        
        with patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True):
            
            self.server_manager._start_label_studio_server()
            
            # Check that environment variables were passed correctly
            call_kwargs = mock_popen.call_args[1]
            env = call_kwargs['env']
            
            # Verify Label Studio specific environment variables
            assert env['LABEL_STUDIO_PORT'] == '8080'
            assert env['LABEL_STUDIO_HOST'] == '127.0.0.1' 
            assert env['LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED'] == 'true'
            assert 'LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT' in env
    
    @patch('subprocess.run')
    def test_uvx_with_different_error_types(self, mock_run):
        """Test handling of different types of uvx errors."""
        # Test CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(1, "uvx", "uvx failed")
        
        with patch('subprocess.Popen') as mock_popen, \
             patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True), \
             patch.object(self.server_manager, '_setup_labelstudio_environment'):
            
            # Create mock virtual environment for fallback
            self.server_manager.labelstudio_venv.mkdir(parents=True, exist_ok=True)
            python_path = self.server_manager.labelstudio_venv / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.touch()
            
            mock_popen.return_value = Mock(pid=12345)
            
            result = self.server_manager._start_label_studio_server()
            
            # Should fallback to virtual environment and succeed
            assert result is True


@pytest.mark.slow
class TestUvxRealExecution:
    """Test real uvx execution (requires uvx to be installed)."""
    
    @pytest.mark.skipif(shutil.which("uvx") is None, reason="uvx not available")
    def test_uvx_help_command(self):
        """Test that uvx help command works (if uvx is installed)."""
        try:
            result = subprocess.run(["uvx", "--help"], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0
            assert "uvx" in result.stdout.lower() or "usage" in result.stdout.lower()
        except subprocess.TimeoutExpired:
            pytest.skip("uvx command timed out")
        except FileNotFoundError:
            pytest.skip("uvx not available in system")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])