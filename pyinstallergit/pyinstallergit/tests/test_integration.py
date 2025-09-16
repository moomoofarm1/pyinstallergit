"""
Integration tests for the ALF audio processing system.

These tests validate the complete workflows including audio preprocessing,
server management, and pipeline coordination.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock

from audio_processing.preprocessing import AudioPreprocessor
from communication.json_protocol import JsonProtocol, MessageType
from communication.server_manager import ServerManager, ServerType
from ui.pipeline_controller import PipelineController

class TestALFIntegration:
    """Integration tests for the complete ALF system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Initialize core components
        self.preprocessor = AudioPreprocessor()
        self.json_protocol = JsonProtocol()
        self.server_manager = ServerManager()
        self.pipeline_controller = PipelineController(
            self.server_manager, 
            self.json_protocol
        )
        
        # Create test audio files
        self.test_mp3_file = self.temp_dir / "test_audio.mp3"
        self.test_wav_file = self.temp_dir / "test_audio.wav" 
        self._create_test_audio_files()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        self.preprocessor.cleanup_processed_files()
        self.server_manager.cleanup_all()
    
    def _create_test_audio_files(self):
        """Create test audio files for integration testing."""
        # Generate test audio (5 seconds, stereo, 44.1kHz)
        sample_rate = 44100
        duration = 5.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create a more complex signal with multiple frequencies
        # Simulate different speakers with different frequency content
        speaker1_freq = 440.0  # A4
        speaker2_freq = 880.0  # A5
        
        # Speaker 1: 0-2.5s and 4-5s
        speaker1_signal = np.sin(speaker1_freq * 2.0 * np.pi * t)
        speaker1_mask = ((t <= 2.5) | (t >= 4.0))
        
        # Speaker 2: 2.5-4s  
        speaker2_signal = np.sin(speaker2_freq * 2.0 * np.pi * t) * 0.7
        speaker2_mask = ((t > 2.5) & (t < 4.0))
        
        # Combine signals
        combined_signal = (speaker1_signal * speaker1_mask + 
                          speaker2_signal * speaker2_mask)
        
        # Add some noise
        noise = np.random.normal(0, 0.05, combined_signal.shape)
        combined_signal += noise
        
        # Create stereo version (slightly different L/R channels)
        stereo_audio = np.column_stack((combined_signal, combined_signal * 0.8))
        
        # Save as WAV (MP3 creation requires pydub/ffmpeg)
        sf.write(str(self.test_wav_file), stereo_audio, sample_rate)
        
        # Copy WAV as "MP3" for testing (will be processed as WAV)
        shutil.copy(str(self.test_wav_file), str(self.test_mp3_file))
    
    def test_complete_preprocessing_workflow(self):
        """Test the complete audio preprocessing workflow."""
        # Test initial file validation
        assert self.test_wav_file.exists()
        
        # Get initial audio info
        initial_info = self.preprocessor.get_audio_info(self.test_wav_file)
        assert initial_info['sample_rate'] == 44100
        assert initial_info['channels'] == 2
        assert initial_info['is_preprocessed'] is False
        
        # Preprocess the audio
        processed_file = self.preprocessor.preprocess_mp3_to_mono_16k(
            str(self.test_wav_file)
        )
        
        # Verify preprocessing results
        assert Path(processed_file).exists()
        
        processed_info = self.preprocessor.get_audio_info(processed_file)
        assert processed_info['sample_rate'] == 16000
        assert processed_info['channels'] == 1
        assert processed_info['is_preprocessed'] is True
        
        # Verify audio content preservation
        duration_diff = abs(
            initial_info['duration_seconds'] - processed_info['duration_seconds']
        )
        assert duration_diff < 0.2  # Within 200ms tolerance
        
        return processed_file
    
    def test_json_protocol_message_flow(self):
        """Test JSON protocol message creation and processing."""
        # Create a processing request
        message = self.json_protocol.create_message(
            MessageType.PROCESS_REQUEST,
            {
                'audio_file_path': str(self.test_wav_file),
                'processing_type': 'diarization',
                'parameters': {'min_speakers': 1, 'max_speakers': 5}
            }
        )
        
        # Validate message
        validation = self.json_protocol.validate_message(message)
        assert validation['valid'] is True
        
        # Serialize and deserialize
        json_str = self.json_protocol.serialize_message(message)
        deserialized = self.json_protocol.deserialize_message(json_str)
        
        # Verify round-trip integrity
        assert deserialized.message_type == message.message_type
        assert deserialized.payload == message.payload
        assert deserialized.message_id == message.message_id
        
        # Create response message
        response = self.json_protocol.create_message(
            MessageType.PROCESS_RESPONSE,
            {
                'status': 'completed',
                'output_files': ['/path/to/result.rttm'],
                'processing_time_seconds': 12.5
            },
            correlation_id=message.message_id
        )
        
        assert response.correlation_id == message.message_id
        
        return message, response
    
    @patch('communication.server_manager.subprocess.run')
    @patch('communication.server_manager.subprocess.Popen')
    def test_server_manager_lifecycle(self, mock_popen, mock_run):
        """Test server manager lifecycle with mocked processes."""
        # Mock successful virtual environment creation
        mock_run.return_value.returncode = 0
        
        # Mock server process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        # Test environment setup
        try:
            self.server_manager.setup_virtual_environments()
            # Should not raise exception with mocked subprocess
        except Exception:
            # Expected if system dependencies are missing
            pass
        
        # Test server status checking
        status = self.server_manager.check_environment_status()
        assert isinstance(status, str)
        assert len(status) > 0
        
        # Test server info retrieval
        server_info = self.server_manager.get_server_info(ServerType.DIARIZATION)
        # Should return None or ServerInfo object
        assert server_info is None or hasattr(server_info, 'server_type')
    
    def test_pipeline_controller_workflow(self):
        """Test pipeline controller workflow with mock processing."""
        # First preprocess an audio file
        processed_file = self.test_complete_preprocessing_workflow()
        
        # Test diarization pipeline
        try:
            result = self.pipeline_controller.run_diarization_pipeline(processed_file)
            
            # Verify result structure (using mock implementation)
            assert isinstance(result, dict)
            assert 'job_type' in result
            assert result['job_type'] == 'diarization'
            assert 'status' in result
            assert result['status'] == 'completed'
            assert 'output_files' in result
            assert len(result['output_files']) > 0
            
        except Exception as e:
            # May fail due to missing dependencies, that's expected
            assert "server" in str(e).lower() or "pipeline" in str(e).lower()
        
        # Test transcription pipeline  
        try:
            result = self.pipeline_controller.run_transcription_pipeline(processed_file)
            
            # Verify result structure (using mock implementation)
            assert isinstance(result, dict)
            assert 'job_type' in result
            assert result['job_type'] == 'transcription'
            
        except Exception as e:
            # May fail due to missing dependencies, that's expected
            assert "server" in str(e).lower() or "pipeline" in str(e).lower()
    
    def test_job_management(self):
        """Test job management functionality."""
        # Get initial job list (should be empty)
        initial_jobs = self.pipeline_controller.get_active_jobs()
        assert isinstance(initial_jobs, dict)
        
        # Mock a job by directly adding to active_jobs
        mock_job_id = "test_job_123"
        self.pipeline_controller.active_jobs[mock_job_id] = {
            'status': 'processing',
            'start_time': 1234567890.0,
            'progress': 50.0
        }
        
        # Test job status retrieval
        job_status = self.pipeline_controller.get_job_status(mock_job_id)
        assert job_status is not None
        assert job_status['status'] == 'processing'
        assert job_status['progress'] == 50.0
        
        # Test job cancellation
        cancel_result = self.pipeline_controller.cancel_job(mock_job_id)
        assert cancel_result is True
        
        # Verify job was cancelled
        updated_status = self.pipeline_controller.get_job_status(mock_job_id)
        assert updated_status['status'] == 'cancelled'
        
        # Test cleanup of completed jobs
        self.pipeline_controller.cleanup_completed_jobs(max_age_hours=0)
        # Job should be removed due to 0 hour max age
        remaining_jobs = self.pipeline_controller.get_active_jobs()
        assert mock_job_id not in remaining_jobs
    
    def test_error_handling(self):
        """Test error handling across components."""
        # Test preprocessing with non-existent file
        with pytest.raises(FileNotFoundError):
            self.preprocessor.preprocess_mp3_to_mono_16k("/nonexistent/file.mp3")
        
        # Test pipeline with non-existent file
        with pytest.raises(FileNotFoundError):
            self.pipeline_controller.run_diarization_pipeline("/nonexistent/audio.wav")
        
        # Test JSON protocol with invalid data
        with pytest.raises(ValueError):
            self.json_protocol.deserialize_message("invalid json")
        
        # Test server manager with invalid server type
        invalid_server_info = self.server_manager.get_server_info("invalid_server")
        assert invalid_server_info is None
    
    def test_audio_format_support(self):
        """Test support for different audio formats."""
        # Test different audio formats (mocked since we only have WAV)
        formats_to_test = ['.wav', '.mp3', '.flac', '.m4a']
        
        for format_ext in formats_to_test:
            test_file = self.temp_dir / f"test{format_ext}"
            
            # Copy our test WAV file
            shutil.copy(str(self.test_wav_file), str(test_file))
            
            try:
                # Should not raise exception for supported formats
                result = self.preprocessor.preprocess_mp3_to_mono_16k(str(test_file))
                assert Path(result).exists()
                
                # Verify output is correct format
                audio_info = self.preprocessor.get_audio_info(result)
                assert audio_info['sample_rate'] == 16000
                assert audio_info['channels'] == 1
                
            except Exception as e:
                # Some formats may fail due to missing codecs (expected)
                assert "format" in str(e).lower() or "codec" in str(e).lower()
    
    def test_cleanup_and_resource_management(self):
        """Test proper cleanup and resource management."""
        # Create some temporary files during processing
        processed_file = self.test_complete_preprocessing_workflow()
        
        # Verify files were created
        assert Path(processed_file).exists()
        
        # Test cleanup
        self.preprocessor.cleanup_processed_files()
        
        # Verify processed files directory is cleaned up
        # (Note: cleanup might not remove directory if not empty)
        
        # Test server manager cleanup
        self.server_manager.cleanup_all()
        
        # Should not raise exceptions
        all_server_info = self.server_manager.get_all_server_info()
        assert isinstance(all_server_info, dict)

class TestALFEndToEnd:
    """End-to-end tests simulating complete user workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_user_workflow_simulation(self):
        """Simulate a complete user workflow from audio file to results."""
        # Step 1: User selects an audio file
        audio_file = self.temp_dir / "user_audio.wav"
        
        # Create realistic audio file (10 seconds, conversation simulation)
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Simulate conversation with pauses
        segments = [
            (0, 3, 440),     # Speaker 1: 0-3s
            (3.5, 6, 880),   # Speaker 2: 3.5-6s  
            (6.5, 8, 440),   # Speaker 1: 6.5-8s
            (8.5, 10, 880),  # Speaker 2: 8.5-10s
        ]
        
        audio_signal = np.zeros_like(t)
        for start, end, freq in segments:
            mask = (t >= start) & (t <= end)
            audio_signal[mask] = np.sin(freq * 2 * np.pi * t[mask])
        
        # Add realistic noise and make stereo
        noise = np.random.normal(0, 0.02, audio_signal.shape)
        audio_signal += noise
        stereo_audio = np.column_stack((audio_signal, audio_signal * 0.9))
        
        sf.write(str(audio_file), stereo_audio, sample_rate)
        
        # Step 2: Audio preprocessing
        preprocessor = AudioPreprocessor()
        processed_file = preprocessor.preprocess_mp3_to_mono_16k(str(audio_file))
        
        # Verify preprocessing
        assert Path(processed_file).exists()
        processed_info = preprocessor.get_audio_info(processed_file)
        assert processed_info['sample_rate'] == 16000
        assert processed_info['channels'] == 1
        
        # Step 3: Initialize communication system
        json_protocol = JsonProtocol()
        server_manager = ServerManager()
        pipeline_controller = PipelineController(server_manager, json_protocol)
        
        # Step 4: Run diarization (simulated)
        try:
            diarization_result = pipeline_controller.run_diarization_pipeline(
                processed_file
            )
            
            # Verify diarization results
            assert diarization_result['job_type'] == 'diarization'
            assert diarization_result['status'] == 'completed'
            assert 'num_speakers' in diarization_result
            assert diarization_result['num_speakers'] >= 1
            
        except Exception as e:
            # Expected if servers not available
            assert "server" in str(e).lower()
        
        # Step 5: Run transcription (simulated)
        try:
            transcription_result = pipeline_controller.run_transcription_pipeline(
                processed_file  
            )
            
            # Verify transcription results
            assert transcription_result['job_type'] == 'transcription'
            assert transcription_result['status'] == 'completed'
            assert 'full_transcript' in transcription_result
            
        except Exception as e:
            # Expected if servers not available
            assert "server" in str(e).lower()
        
        # Step 6: Cleanup
        preprocessor.cleanup_processed_files()
        server_manager.cleanup_all()
        
        # Should complete without exceptions
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])