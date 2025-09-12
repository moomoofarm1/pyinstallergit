"""
Test Label Studio startup functionality with uvx and fallback approaches.

Tests the Label Studio server startup in both uvx and virtual environment modes,
ensuring proper command generation, environment setup, and process management.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os

from communication.server_manager import ServerManager, ServerType, ServerState
from communication.json_protocol import JsonProtocol


class TestLabelStudioStartup:
    """Test Label Studio server startup functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.server_manager = ServerManager()
        # Use temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.server_manager.venv_dir = Path(self.temp_dir) / "alf_venvs"
        self.server_manager.labelstudio_venv = self.server_manager.venv_dir / "labelstudio"
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clean up any running processes
        if hasattr(self, 'server_manager'):
            self.server_manager.cleanup()
    
    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_labelstudio_startup_with_uvx(self, mock_popen, mock_run):
        """Test Label Studio startup using uvx approach."""
        # Mock uvx being available
        mock_run.return_value = Mock(returncode=0)
        
        # Mock successful process start
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Mock health check methods
        with patch.object(self.server_manager, '_wait_for_server_startup', return_value=True), \
             patch.object(self.server_manager, '_start_health_monitor'), \
             patch.object(self.server_manager, 'is_server_running', return_value=False):
            
            result = self.server_manager._start_label_studio_server()
            
            assert result is True
            
            # Verify uvx command was used
            expected_cmd = [
                "uvx", "label-studio", "start", "diarization_project",
                "--host", "127.0.0.1",
                "--port", "8080", 
                "--data-dir", str(Path("label_studio_projects"))
            ]
            
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert call_args[0][0] == expected_cmd
    
    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_labelstudio_startup_fallback_to_venv(self, mock_popen, mock_run):
        """Test Label Studio startup falling back to virtual environment."""
        # Mock uvx not being available
        mock_run.side_effect = FileNotFoundError("uvx not found")
        
        # Create mock virtual environment
        self.server_manager.labelstudio_venv.mkdir(parents=True, exist_ok=True)
        python_path = self.server_manager.labelstudio_venv / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
        python_path.parent.mkdir(parents=True, exist_ok=True)
        python_path.touch()
        
        # Mock successful process start
        mock_process = Mock()
        mock_process.pid = 12346
        mock_popen.return_value = mock_process
        
        with patch.object(self.server_manager, '_wait_for_server_startup', return_value=True), \
             patch.object(self.server_manager, '_start_health_monitor'), \
             patch.object(self.server_manager, 'is_server_running', return_value=False):
            
            result = self.server_manager._start_label_studio_server()
            
            assert result is True
            
            # Verify virtual environment command was used
            expected_cmd = [
                str(python_path), '-m', 'label_studio', 
                'start', 'diarization_project',
                '--host', '127.0.0.1',
                '--port', '8080', 
                '--data-dir', str(Path("label_studio_projects"))
            ]
            
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert call_args[0][0] == expected_cmd
    
    @patch('subprocess.run')
    def test_uvx_availability_check(self, mock_run):
        """Test uvx availability checking."""
        # Test uvx available
        mock_run.return_value = Mock(returncode=0)
        
        with patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True), \
             patch('subprocess.Popen') as mock_popen:
            
            mock_popen.return_value = Mock(pid=12345)
            self.server_manager._start_label_studio_server()
            
            # Should call uvx --version check
            mock_run.assert_called_with(["uvx", "--version"], capture_output=True, check=True)
    
    @patch('subprocess.run')
    def test_environment_setup_fallback(self, mock_run):
        """Test environment setup when uvx is not available."""
        # Mock uvx not available
        mock_run.side_effect = FileNotFoundError("uvx not found")
        
        with patch.object(self.server_manager, '_setup_labelstudio_environment') as mock_setup, \
             patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True), \
             patch('subprocess.Popen'):
            
            self.server_manager._start_label_studio_server()
            
            # Should call environment setup when venv doesn't exist
            mock_setup.assert_called_once()
    
    def test_server_already_running(self):
        """Test behavior when Label Studio server is already running."""
        with patch.object(self.server_manager, 'is_server_running', return_value=True):
            result = self.server_manager._start_label_studio_server()
            
            assert result is True
    
    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_server_startup_failure(self, mock_popen, mock_run):
        """Test handling of server startup failure."""
        # Mock uvx available
        mock_run.return_value = Mock(returncode=0)
        
        # Mock process that fails to start
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_popen.return_value = mock_process
        
        with patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=False), \
             patch.object(self.server_manager, '_cleanup_failed_process'):
            
            result = self.server_manager._start_label_studio_server()
            
            assert result is False
            
            # Verify server state is set to error
            assert self.server_manager.servers[ServerType.LABEL_STUDIO].state == ServerState.ERROR
    
    def test_integrated_diarization_server_startup(self):
        """Test that starting diarization server also starts Label Studio."""
        with patch.object(self.server_manager, '_start_server', return_value=True) as mock_start_server, \
             patch.object(self.server_manager, '_start_label_studio_server', return_value=True) as mock_start_ls:
            
            result = self.server_manager.start_diarization_server(with_label_studio=True)
            
            assert result is True
            mock_start_server.assert_called_once_with(ServerType.DIARIZATION)
            mock_start_ls.assert_called_once()
    
    def test_environment_variables_setup(self):
        """Test that proper environment variables are set for Label Studio."""
        with patch('subprocess.run') as mock_run, \
             patch('subprocess.Popen') as mock_popen, \
             patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True):
            
            mock_run.return_value = Mock(returncode=0)  # uvx available
            mock_popen.return_value = Mock(pid=12345)
            
            self.server_manager._start_label_studio_server()
            
            # Check environment variables were set
            call_kwargs = mock_popen.call_args[1]
            env = call_kwargs['env']
            
            assert env['LABEL_STUDIO_PORT'] == '8080'
            assert env['LABEL_STUDIO_HOST'] == '127.0.0.1'
            assert env['LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED'] == 'true'
            assert 'LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT' in env


@pytest.mark.integration
class TestLabelStudioIntegration:
    """Integration tests for Label Studio functionality."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.server_manager = ServerManager()
    
    def teardown_method(self):
        """Clean up after integration tests."""
        if hasattr(self, 'server_manager'):
            self.server_manager.cleanup()
    
    def test_uvx_command_structure(self):
        """Test that uvx command structure matches expected format."""
        expected_command = [
            "uvx", "label-studio", "start", "diarization_project",
            "--host", "127.0.0.1",
            "--port", "8080", 
            "--data-dir", str(Path("label_studio_projects"))
        ]
        
        with patch('subprocess.run') as mock_run, \
             patch('subprocess.Popen') as mock_popen, \
             patch.object(self.server_manager, 'is_server_running', return_value=False), \
             patch.object(self.server_manager, '_wait_for_server_startup', return_value=True):
            
            mock_run.return_value = Mock(returncode=0)  # uvx available
            mock_popen.return_value = Mock(pid=12345)
            
            self.server_manager._start_label_studio_server()
            
            # Verify command structure
            actual_command = mock_popen.call_args[0][0]
            assert actual_command == expected_command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])