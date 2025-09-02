"""
Audio Preprocessing Module

This module handles audio preprocessing tasks including:
- MP3 to WAV conversion
- Stereo to mono channel extraction
- Downsampling to 16KHz sample rate
- Audio format normalization for ML pipelines

The preprocessing ensures that all audio files are in the optimal format
for both diarization (pyannote.audio) and transcription (NeMo ASR) pipelines.
"""

import os
import librosa
import soundfile as sf
from pathlib import Path
from typing import Union, Optional
import logging
from pydub import AudioSegment
import numpy as np

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """
    Audio preprocessing class for converting and normalizing audio files.
    
    This class provides methods to convert MP3 files to the standardized
    format required by the ML pipelines: 16KHz mono WAV files.
    """
    
    def __init__(self, target_sample_rate: int = 16000, target_channels: int = 1):
        """
        Initialize the audio preprocessor.
        
        Args:
            target_sample_rate (int): Target sample rate in Hz (default: 16000)
            target_channels (int): Target number of channels (default: 1 for mono)
        """
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels
        
        # Create output directory for processed files
        self.output_dir = Path("processed_audio")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"AudioPreprocessor initialized: {target_sample_rate}Hz, {target_channels} channels")
    
    def preprocess_mp3_to_mono_16k(self, input_path: Union[str, Path]) -> str:
        """
        Convert MP3 file to 16KHz mono WAV format.
        
        This method performs the complete preprocessing pipeline:
        1. Load MP3 file
        2. Convert to mono if stereo
        3. Resample to 16KHz
        4. Save as WAV file
        5. Apply audio normalization
        
        Args:
            input_path (Union[str, Path]): Path to input MP3 file
            
        Returns:
            str: Path to the processed WAV file
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If input file is not a valid audio file
            RuntimeError: If preprocessing fails
        """
        input_path = Path(input_path)
        
        # Validate input file
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not input_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.m4a']:
            raise ValueError(f"Unsupported audio format: {input_path.suffix}")
        
        # Generate output filename
        output_filename = f"{input_path.stem}_16k_mono.wav"
        output_path = self.output_dir / output_filename
        
        try:
            logger.info(f"Starting preprocessing: {input_path.name}")
            
            # Method 1: Use pydub for initial conversion (handles MP3 better)
            if input_path.suffix.lower() == '.mp3':
                audio_segment = AudioSegment.from_mp3(str(input_path))
                
                # Convert to mono if stereo
                if audio_segment.channels > 1:
                    audio_segment = audio_segment.set_channels(1)
                    logger.info("Converted stereo to mono")
                
                # Convert to target sample rate
                if audio_segment.frame_rate != self.target_sample_rate:
                    audio_segment = audio_segment.set_frame_rate(self.target_sample_rate)
                    logger.info(f"Resampled to {self.target_sample_rate}Hz")
                
                # Export as WAV
                audio_segment.export(str(output_path), format="wav")
                logger.info(f"Exported to WAV: {output_path.name}")
                
            else:
                # Method 2: Use librosa for other formats (more precise)
                audio_data, original_sr = librosa.load(
                    str(input_path), 
                    sr=self.target_sample_rate,  # Automatically resample
                    mono=True  # Convert to mono
                )
                
                # Save as WAV file
                sf.write(str(output_path), audio_data, self.target_sample_rate)
                logger.info(f"Processed using librosa: {output_path.name}")
            
            # Post-processing validation and normalization
            self._validate_and_normalize_output(output_path)
            
            # Log file statistics
            self._log_audio_statistics(input_path, output_path)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Preprocessing failed for {input_path.name}: {e}")
            # Clean up partial output file if it exists
            if output_path.exists():
                output_path.unlink()
            raise RuntimeError(f"Audio preprocessing failed: {e}")
    
    def _validate_and_normalize_output(self, output_path: Path):
        """
        Validate and normalize the processed audio file.
        
        This method ensures the output file meets quality standards:
        - Correct sample rate and channels
        - Appropriate audio levels
        - No clipping or distortion
        
        Args:
            output_path (Path): Path to the processed audio file
        """
        try:
            # Load and validate the processed file
            audio_data, sample_rate = librosa.load(str(output_path), sr=None, mono=False)
            
            # Validate sample rate
            if sample_rate != self.target_sample_rate:
                logger.warning(f"Sample rate mismatch: expected {self.target_sample_rate}, got {sample_rate}")
            
            # Validate channels (librosa loads as mono by default, but let's be explicit)
            if len(audio_data.shape) > 1:
                logger.warning(f"Expected mono audio, got {audio_data.shape[0]} channels")
            
            # Check for audio quality issues
            if np.max(np.abs(audio_data)) == 0:
                raise ValueError("Output audio is silent (all zeros)")
            
            # Check for clipping (values at maximum range)
            clipping_ratio = np.sum(np.abs(audio_data) >= 0.99) / len(audio_data)
            if clipping_ratio > 0.01:  # More than 1% clipping
                logger.warning(f"Audio clipping detected: {clipping_ratio*100:.2f}% of samples")
            
            # Apply gentle normalization if needed (prevent clipping, maintain dynamics)
            max_amplitude = np.max(np.abs(audio_data))
            if max_amplitude > 0.95:
                # Scale down to prevent clipping
                normalization_factor = 0.95 / max_amplitude
                audio_data = audio_data * normalization_factor
                
                # Save the normalized version
                sf.write(str(output_path), audio_data, sample_rate)
                logger.info(f"Applied normalization factor: {normalization_factor:.3f}")
            
            logger.info(f"Output validation successful: {output_path.name}")
            
        except Exception as e:
            logger.error(f"Output validation failed: {e}")
            raise
    
    def _log_audio_statistics(self, input_path: Path, output_path: Path):
        """
        Log statistics about the audio processing.
        
        Args:
            input_path (Path): Original input file path
            output_path (Path): Processed output file path
        """
        try:
            # Input file stats
            input_size = input_path.stat().st_size / (1024 * 1024)  # MB
            
            # Output file stats
            output_size = output_path.stat().st_size / (1024 * 1024)  # MB
            output_data, output_sr = librosa.load(str(output_path), sr=None)
            duration = len(output_data) / output_sr
            
            logger.info(f"Processing statistics:")
            logger.info(f"  Input file: {input_path.name} ({input_size:.2f} MB)")
            logger.info(f"  Output file: {output_path.name} ({output_size:.2f} MB)")
            logger.info(f"  Duration: {duration:.2f} seconds")
            logger.info(f"  Sample rate: {output_sr} Hz")
            logger.info(f"  Channels: mono")
            
        except Exception as e:
            logger.warning(f"Could not gather audio statistics: {e}")
    
    def batch_preprocess(self, input_directory: Union[str, Path], 
                        file_extensions: Optional[list] = None) -> list:
        """
        Preprocess multiple audio files in a directory.
        
        Args:
            input_directory (Union[str, Path]): Directory containing audio files
            file_extensions (Optional[list]): List of file extensions to process
                                            (default: ['.mp3', '.wav', '.flac', '.m4a'])
        
        Returns:
            list: List of paths to processed files
        """
        if file_extensions is None:
            file_extensions = ['.mp3', '.wav', '.flac', '.m4a']
        
        input_dir = Path(input_directory)
        if not input_dir.exists() or not input_dir.is_dir():
            raise ValueError(f"Invalid input directory: {input_dir}")
        
        processed_files = []
        
        # Find all audio files
        audio_files = []
        for ext in file_extensions:
            audio_files.extend(input_dir.glob(f"*{ext}"))
            audio_files.extend(input_dir.glob(f"*{ext.upper()}"))
        
        logger.info(f"Found {len(audio_files)} audio files to process")
        
        # Process each file
        for audio_file in audio_files:
            try:
                processed_path = self.preprocess_mp3_to_mono_16k(audio_file)
                processed_files.append(processed_path)
                logger.info(f"Successfully processed: {audio_file.name}")
            except Exception as e:
                logger.error(f"Failed to process {audio_file.name}: {e}")
                continue
        
        logger.info(f"Batch processing completed: {len(processed_files)}/{len(audio_files)} files")
        return processed_files
    
    def get_audio_info(self, audio_path: Union[str, Path]) -> dict:
        """
        Get detailed information about an audio file.
        
        Args:
            audio_path (Union[str, Path]): Path to audio file
            
        Returns:
            dict: Dictionary containing audio file information
        """
        audio_path = Path(audio_path)
        
        try:
            # Load audio metadata
            audio_data, sample_rate = librosa.load(str(audio_path), sr=None, mono=False)
            
            # Calculate statistics
            duration = len(audio_data) / sample_rate if len(audio_data.shape) == 1 else len(audio_data[0]) / sample_rate
            file_size = audio_path.stat().st_size / (1024 * 1024)  # MB
            
            # Handle stereo/mono
            if len(audio_data.shape) == 1:
                channels = 1
                rms_level = np.sqrt(np.mean(audio_data**2))
                peak_level = np.max(np.abs(audio_data))
            else:
                channels = audio_data.shape[0]
                rms_level = np.sqrt(np.mean(audio_data**2))
                peak_level = np.max(np.abs(audio_data))
            
            return {
                'filename': audio_path.name,
                'duration_seconds': round(duration, 2),
                'sample_rate': sample_rate,
                'channels': channels,
                'file_size_mb': round(file_size, 2),
                'rms_level': round(float(rms_level), 4),
                'peak_level': round(float(peak_level), 4),
                'format': audio_path.suffix.lower(),
                'is_preprocessed': sample_rate == self.target_sample_rate and channels == 1
            }
            
        except Exception as e:
            logger.error(f"Could not get audio info for {audio_path}: {e}")
            return {'error': str(e)}
    
    def cleanup_processed_files(self):
        """Clean up all processed audio files."""
        if self.output_dir.exists():
            for file in self.output_dir.glob("*.wav"):
                file.unlink()
                logger.info(f"Deleted processed file: {file.name}")
            
            # Remove directory if empty
            try:
                self.output_dir.rmdir()
                logger.info("Cleaned up processed audio directory")
            except OSError:
                pass  # Directory not empty, that's okay