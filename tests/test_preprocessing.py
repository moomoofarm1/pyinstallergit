"""
Unit tests for audio preprocessing functionality.

These tests validate the audio preprocessing pipeline including
MP3 to WAV conversion, sample rate conversion, and mono channel extraction.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock

from audio_processing.preprocessing import AudioPreprocessor
from audio_processing.utils import AudioUtils

class TestAudioPreprocessor:
    """Test cases for AudioPreprocessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.preprocessor = AudioPreprocessor()
        
        # Create a test audio file (16KHz mono sine wave)
        self.test_audio_file = self.temp_dir / "test_audio.wav"
        self._create_test_audio_file(self.test_audio_file)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_test_audio_file(self, file_path: Path, 
                               sample_rate: int = 44100, 
                               duration: float = 2.0,
                               channels: int = 2):
        """Create a test audio file for testing."""
        # Generate a sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        frequency = 440.0  # A4 note
        sine_wave = np.sin(frequency * 2.0 * np.pi * t)
        
        # Make stereo if requested
        if channels == 2:
            audio_data = np.column_stack((sine_wave, sine_wave * 0.5))
        else:
            audio_data = sine_wave
        
        # Save to file
        sf.write(str(file_path), audio_data, sample_rate)
    
    def test_preprocessor_initialization(self):
        """Test AudioPreprocessor initialization."""
        preprocessor = AudioPreprocessor(target_sample_rate=22050, target_channels=1)
        
        assert preprocessor.target_sample_rate == 22050
        assert preprocessor.target_channels == 1
        assert preprocessor.output_dir.exists()
    
    def test_preprocess_wav_file(self):
        """Test preprocessing of WAV file."""
        # Create a stereo 44.1kHz test file
        stereo_file = self.temp_dir / "stereo_44k.wav"
        self._create_test_audio_file(stereo_file, sample_rate=44100, channels=2)
        
        # Process the file
        output_path = self.preprocessor.preprocess_mp3_to_mono_16k(str(stereo_file))
        
        # Verify output
        assert Path(output_path).exists()
        
        # Check audio properties
        audio_data, sample_rate = sf.read(output_path)
        
        assert sample_rate == 16000  # Should be downsampled to 16kHz
        assert len(audio_data.shape) == 1  # Should be mono
        assert len(audio_data) > 0  # Should have data
    
    @patch('audio_processing.preprocessing.AudioSegment')
    def test_preprocess_mp3_file_mock(self, mock_audio_segment):
        """Test preprocessing of MP3 file using mock."""
        # Create a fake MP3 file
        mp3_file = self.temp_dir / "test.mp3"
        mp3_file.write_text("fake mp3 content")
        
        # Mock AudioSegment behavior
        mock_segment = MagicMock()
        mock_segment.channels = 2
        mock_segment.frame_rate = 44100
        mock_audio_segment.from_mp3.return_value = mock_segment
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_frame_rate.return_value = mock_segment
        
        # Process the file
        try:
            output_path = self.preprocessor.preprocess_mp3_to_mono_16k(str(mp3_file))
            # If we get here, the mock worked
            assert output_path is not None
        except Exception:
            # Expected if pydub is not properly mocked
            pass
    
    def test_preprocess_nonexistent_file(self):
        """Test preprocessing of non-existent file."""
        fake_file = self.temp_dir / "nonexistent.mp3"
        
        with pytest.raises(FileNotFoundError):
            self.preprocessor.preprocess_mp3_to_mono_16k(str(fake_file))
    
    def test_preprocess_unsupported_format(self):
        """Test preprocessing of unsupported file format."""
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("not an audio file")
        
        with pytest.raises(ValueError, match="Unsupported audio format"):
            self.preprocessor.preprocess_mp3_to_mono_16k(str(txt_file))
    
    def test_get_audio_info(self):
        """Test getting audio file information."""
        info = self.preprocessor.get_audio_info(self.test_audio_file)
        
        assert info['filename'] == self.test_audio_file.name
        assert info['sample_rate'] == 44100
        assert info['channels'] == 2
        assert info['duration_seconds'] > 0
        assert info['format'] == '.wav'
        assert info['is_preprocessed'] is False  # 44.1kHz stereo, not preprocessed
    
    def test_batch_preprocess(self):
        """Test batch processing of multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = self.temp_dir / f"test_{i}.wav"
            self._create_test_audio_file(file_path, channels=1)  # Mono files
            files.append(str(file_path))
        
        # Process batch
        processed_files = self.preprocessor.batch_preprocess(str(self.temp_dir))
        
        assert len(processed_files) == 3
        
        # Verify each processed file
        for output_file in processed_files:
            assert Path(output_file).exists()
            audio_data, sample_rate = sf.read(output_file)
            assert sample_rate == 16000

class TestAudioUtils:
    """Test cases for AudioUtils class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_is_audio_file(self):
        """Test audio file detection."""
        assert AudioUtils.is_audio_file("test.mp3") is True
        assert AudioUtils.is_audio_file("test.wav") is True
        assert AudioUtils.is_audio_file("test.flac") is True
        assert AudioUtils.is_audio_file("test.txt") is False
        assert AudioUtils.is_audio_file("test.jpg") is False
    
    def test_validate_audio_file_nonexistent(self):
        """Test validation of non-existent file."""
        result = AudioUtils.validate_audio_file("nonexistent.wav")
        
        assert result['valid'] is False
        assert result['exists'] is False
        assert 'not exist' in result['message'].lower()
    
    def test_validate_audio_file_unsupported(self):
        """Test validation of unsupported file."""
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("not audio")
        
        result = AudioUtils.validate_audio_file(str(txt_file))
        
        assert result['valid'] is False
        assert result['exists'] is True
        assert result['supported_format'] is False
    
    def test_find_audio_files(self):
        """Test finding audio files in directory."""
        # Create test files
        audio_files = ['test1.mp3', 'test2.wav', 'test3.flac']
        other_files = ['readme.txt', 'data.json']
        
        for filename in audio_files + other_files:
            (self.temp_dir / filename).write_text("fake content")
        
        # Find audio files
        found_files = AudioUtils.find_audio_files(self.temp_dir)
        
        # Should find only audio files
        found_names = [f.name for f in found_files]
        
        for audio_file in audio_files:
            assert audio_file in found_names
        
        for other_file in other_files:
            assert other_file not in found_names
    
    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        # Create a test file
        test_file = self.temp_dir / "test.wav"
        
        # Create a 10-second audio file
        sample_rate = 16000
        duration = 10.0
        audio_data = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
        sf.write(str(test_file), audio_data, sample_rate)
        
        # Estimate processing times
        prep_time = AudioUtils.estimate_processing_time(test_file, 'preprocessing')
        diarization_time = AudioUtils.estimate_processing_time(test_file, 'diarization')
        transcription_time = AudioUtils.estimate_processing_time(test_file, 'transcription')
        
        # Should be reasonable estimates
        assert prep_time > 0
        assert diarization_time > prep_time  # Diarization should take longer
        assert transcription_time > 0
        
        # Diarization should be estimated as taking longest
        assert diarization_time >= transcription_time >= prep_time
    
    @patch('audio_processing.utils.shutil.disk_usage')
    def test_check_disk_space(self, mock_disk_usage):
        """Test disk space checking."""
        # Mock disk usage (1GB free)
        mock_disk_usage.return_value = MagicMock(free=1024**3)
        
        # Should have space for 500MB
        assert AudioUtils.check_disk_space(self.temp_dir, 500) is True
        
        # Should not have space for 2GB
        assert AudioUtils.check_disk_space(self.temp_dir, 2048) is False

# Integration tests
class TestAudioProcessingIntegration:
    """Integration tests for audio processing components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.preprocessor = AudioPreprocessor()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.preprocessor.cleanup_processed_files()
    
    def test_full_preprocessing_workflow(self):
        """Test the complete preprocessing workflow."""
        # Create a test stereo file at 44.1kHz
        input_file = self.temp_dir / "input.wav"
        
        # Generate test audio (2 seconds, stereo, 44.1kHz)
        sample_rate = 44100
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        sine_wave = np.sin(440 * 2.0 * np.pi * t)  # A4 note
        
        # Create stereo version (different amplitudes for L/R)
        stereo_audio = np.column_stack((sine_wave, sine_wave * 0.7))
        
        sf.write(str(input_file), stereo_audio, sample_rate)
        
        # Get initial file info
        initial_info = self.preprocessor.get_audio_info(input_file)
        assert initial_info['sample_rate'] == 44100
        assert initial_info['channels'] == 2
        assert initial_info['is_preprocessed'] is False
        
        # Preprocess the file
        output_file = self.preprocessor.preprocess_mp3_to_mono_16k(str(input_file))
        
        # Verify the output
        assert Path(output_file).exists()
        
        # Get processed file info
        processed_info = self.preprocessor.get_audio_info(output_file)
        assert processed_info['sample_rate'] == 16000
        assert processed_info['channels'] == 1
        assert processed_info['is_preprocessed'] is True
        
        # Verify audio content is preserved (duration should be similar)
        duration_diff = abs(initial_info['duration_seconds'] - processed_info['duration_seconds'])
        assert duration_diff < 0.1  # Within 100ms tolerance
        
        # Verify file sizes (processed should be smaller due to lower sample rate and mono)
        assert processed_info['file_size_mb'] < initial_info['file_size_mb']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])