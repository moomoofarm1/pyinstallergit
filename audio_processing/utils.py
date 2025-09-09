"""
Audio Processing Utilities

This module provides utility functions for audio processing tasks,
including format validation, file management, and audio analysis helpers.
"""

import os
from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional
import logging
import json
from datetime import datetime
import numpy as np
import shutil
import soundfile as sf

logger = logging.getLogger(__name__)

def _load_dependencies():
    """Lazily import heavy optional dependencies."""
    global librosa, np
    if 'librosa' in globals() and 'np' in globals():
        return
    try:
        import librosa  # type: ignore
        import numpy as np  # type: ignore
        globals()['librosa'] = librosa
        globals()['np'] = np
    except ImportError as e:
        raise RuntimeError(
            "Audio utilities require 'librosa' and 'numpy'. "
            "Please run 'Setup All Environments' to install dependencies."
        ) from e

class AudioUtils:
    """
    Utility class for common audio processing operations.
    """
    
    # Supported audio formats
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac']
    
    # Standard sample rates used in audio processing
    STANDARD_SAMPLE_RATES = [8000, 16000, 22050, 44100, 48000]
    
    @staticmethod
    def is_audio_file(file_path: Union[str, Path]) -> bool:
        """
        Check if a file is a supported audio format.
        
        Args:
            file_path (Union[str, Path]): Path to the file
            
        Returns:
            bool: True if file is a supported audio format
        """
        path = Path(file_path)
        return path.suffix.lower() in AudioUtils.SUPPORTED_FORMATS
    
    @staticmethod
    def validate_audio_file(file_path: Union[str, Path]) -> Dict[str, Union[bool, str]]:
        """
        Validate an audio file for processing compatibility.
        
        Args:
            file_path (Union[str, Path]): Path to audio file
            
        Returns:
            Dict: Validation results with status and messages
        """
        path = Path(file_path)
        result = {
            'valid': False,
            'exists': False,
            'readable': False,
            'supported_format': False,
            'loadable': False,
            'message': '',
            'warnings': []
        }
        
        try:
            # Check file existence
            if not path.exists():
                result['message'] = 'File does not exist'
                return result
            result['exists'] = True
            
            # Check readability
            if not os.access(path, os.R_OK):
                result['message'] = 'File is not readable'
                return result
            result['readable'] = True
            
            # Check format support
            if not AudioUtils.is_audio_file(path):
                result['message'] = f'Unsupported format: {path.suffix}'
                return result
            result['supported_format'] = True
            
            # Try to load the file
            try:
                _load_dependencies()
                audio_data, sr = librosa.load(str(path), sr=None, duration=1.0)  # Load only 1 second for testing
                result['loadable'] = True
                
                # Additional checks
                if len(audio_data) == 0:
                    result['warnings'].append('Audio file appears to be empty or very short')
                
                if sr not in AudioUtils.STANDARD_SAMPLE_RATES:
                    result['warnings'].append(f'Unusual sample rate: {sr} Hz')
                
                result['valid'] = True
                result['message'] = 'Audio file is valid'
                
            except Exception as e:
                result['message'] = f'Cannot load audio file: {str(e)}'
                return result
                
        except Exception as e:
            result['message'] = f'Validation error: {str(e)}'
        
        return result
    
    @staticmethod
    def get_audio_duration(file_path: Union[str, Path]) -> Optional[float]:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            file_path (Union[str, Path]): Path to audio file
            
        Returns:
            Optional[float]: Duration in seconds, None if error
        """
        try:
            data, sr = sf.read(str(file_path))
            return data.shape[0] / sr
        except Exception as e:
            logger.error(f"Could not get duration for {file_path}: {e}")
            return None
    
    @staticmethod
    def analyze_audio_quality(audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """
        Analyze audio quality metrics.
        
        Args:
            audio_data (np.ndarray): Audio signal data
            sample_rate (int): Sample rate of the audio
            
        Returns:
            Dict[str, float]: Quality metrics
        """
        try:
            _load_dependencies()

            # Basic statistics
            rms = np.sqrt(np.mean(audio_data**2))
            peak = np.max(np.abs(audio_data))

            # Dynamic range
            db_range = 20 * np.log10(peak / (rms + 1e-10))

            # Zero crossing rate (indicator of speech vs music)
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            avg_zcr = np.mean(zcr)

            # Spectral centroid (brightness indicator)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
            avg_centroid = np.mean(spectral_centroids)

            # MFCC features (relevant for speech)
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
            
            return {
                'rms_level': float(rms),
                'peak_level': float(peak),
                'dynamic_range_db': float(db_range),
                'zero_crossing_rate': float(avg_zcr),
                'spectral_centroid_hz': float(avg_centroid),
                'silence_ratio': float(np.sum(np.abs(audio_data) < 0.01) / len(audio_data)),
                'clipping_ratio': float(np.sum(np.abs(audio_data) >= 0.99) / len(audio_data)),
                'mfcc_mean': mfcc_mean.tolist()
            }
            
        except Exception as e:
            logger.error(f"Audio quality analysis failed: {e}")
            return {}
    
    @staticmethod
    def create_processing_report(input_file: Union[str, Path], 
                               output_file: Union[str, Path],
                               processing_params: Dict) -> Dict:
        """
        Create a detailed processing report.
        
        Args:
            input_file (Union[str, Path]): Original input file
            output_file (Union[str, Path]): Processed output file
            processing_params (Dict): Parameters used in processing
            
        Returns:
            Dict: Processing report
        """
        try:
            input_path = Path(input_file)
            output_path = Path(output_file)
            
            # Get file information
            input_size = input_path.stat().st_size
            output_size = output_path.stat().st_size
            
            # Get audio information
            input_duration = AudioUtils.get_audio_duration(input_path)
            output_duration = AudioUtils.get_audio_duration(output_path)
            
            # Load audio for quality analysis
            try:
                _load_dependencies()
                input_audio, input_sr = librosa.load(str(input_path), sr=None, duration=5.0)  # Analyze first 5 seconds
                output_audio, output_sr = librosa.load(str(output_path), sr=None, duration=5.0)

                input_quality = AudioUtils.analyze_audio_quality(input_audio, input_sr)
                output_quality = AudioUtils.analyze_audio_quality(output_audio, output_sr)
            except Exception as e:
                logger.warning(f"Quality analysis skipped: {e}")
                input_quality = {}
                output_quality = {}
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'processing_params': processing_params,
                'input_file': {
                    'path': str(input_path),
                    'size_bytes': input_size,
                    'size_mb': round(input_size / (1024 * 1024), 2),
                    'duration_seconds': input_duration,
                    'quality_metrics': input_quality
                },
                'output_file': {
                    'path': str(output_path),
                    'size_bytes': output_size,
                    'size_mb': round(output_size / (1024 * 1024), 2),
                    'duration_seconds': output_duration,
                    'quality_metrics': output_quality
                },
                'processing_summary': {
                    'size_reduction_percent': round(((input_size - output_size) / input_size) * 100, 2) if input_size > 0 else 0,
                    'duration_preserved': abs(input_duration - output_duration) < 0.1 if input_duration and output_duration else None,
                    'format_changed': input_path.suffix.lower() != output_path.suffix.lower(),
                    'quality_preserved': True  # TODO: Implement quality comparison logic
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Could not create processing report: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def save_processing_report(report: Dict, report_file: Union[str, Path]):
        """
        Save processing report to JSON file.
        
        Args:
            report (Dict): Processing report dictionary
            report_file (Union[str, Path]): Path to save the report
        """
        try:
            report_path = Path(report_file)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Processing report saved: {report_path}")
            
        except Exception as e:
            logger.error(f"Could not save processing report: {e}")
    
    @staticmethod
    def find_audio_files(directory: Union[str, Path], 
                        recursive: bool = False,
                        extensions: Optional[List[str]] = None) -> List[Path]:
        """
        Find all audio files in a directory.
        
        Args:
            directory (Union[str, Path]): Directory to search
            recursive (bool): Search subdirectories recursively
            extensions (Optional[List[str]]): List of extensions to search for
            
        Returns:
            List[Path]: List of audio file paths
        """
        if extensions is None:
            extensions = AudioUtils.SUPPORTED_FORMATS
        
        directory = Path(directory)
        audio_files = []
        
        try:
            if recursive:
                for ext in extensions:
                    audio_files.extend(directory.rglob(f"*{ext}"))
                    audio_files.extend(directory.rglob(f"*{ext.upper()}"))
            else:
                for ext in extensions:
                    audio_files.extend(directory.glob(f"*{ext}"))
                    audio_files.extend(directory.glob(f"*{ext.upper()}"))
            
            # Remove duplicates and sort
            audio_files = sorted(list(set(audio_files)))
            
            logger.info(f"Found {len(audio_files)} audio files in {directory}")
            
        except Exception as e:
            logger.error(f"Error finding audio files: {e}")
        
        return audio_files
    
    @staticmethod
    def estimate_processing_time(file_path: Union[str, Path], 
                               processing_type: str = 'preprocessing') -> float:
        """
        Estimate processing time for an audio file.
        
        Args:
            file_path (Union[str, Path]): Path to audio file
            processing_type (str): Type of processing ('preprocessing', 'diarization', 'transcription')
            
        Returns:
            float: Estimated processing time in seconds
        """
        try:
            duration = AudioUtils.get_audio_duration(file_path)
            if duration is None:
                return 0.0
            
            # Rough time estimates based on typical processing speeds
            time_multipliers = {
                'preprocessing': 0.1,    # ~10% of audio duration
                'diarization': 0.5,      # ~50% of audio duration
                'transcription': 0.3     # ~30% of audio duration
            }
            
            multiplier = time_multipliers.get(processing_type, 0.2)
            estimated_time = duration * multiplier
            
            # Add base overhead
            estimated_time += 5.0
            
            return max(estimated_time, 1.0)  # Minimum 1 second
            
        except Exception as e:
            logger.error(f"Could not estimate processing time: {e}")
            return 30.0  # Default estimate
    
    @staticmethod
    def check_disk_space(directory: Union[str, Path], required_mb: float) -> bool:
        """
        Check if sufficient disk space is available.
        
        Args:
            directory (Union[str, Path]): Directory to check
            required_mb (float): Required space in MB
            
        Returns:
            bool: True if sufficient space is available
        """
        try:
            free_bytes = shutil.disk_usage(directory).free
            free_mb = free_bytes / (1024 * 1024)
            
            return free_mb >= required_mb
            
        except Exception as e:
            logger.error(f"Could not check disk space: {e}")
            return True  # Assume space is available if check fails
    
    @staticmethod
    def cleanup_temp_files(pattern: str = "temp_audio_*"):
        """
        Clean up temporary audio files.
        
        Args:
            pattern (str): File pattern to match for cleanup
        """
        try:
            import glob
            import tempfile
            
            temp_dir = Path(tempfile.gettempdir())
            temp_files = list(temp_dir.glob(pattern))
            
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                    logger.info(f"Cleaned up temp file: {temp_file.name}")
                except:
                    pass  # Ignore errors during cleanup
                    
        except Exception as e:
            logger.error(f"Temp file cleanup error: {e}")

class AudioMetadata:
    """
    Class for handling audio metadata and processing history.
    """
    
    def __init__(self, audio_file: Union[str, Path]):
        """
        Initialize metadata handler for an audio file.
        
        Args:
            audio_file (Union[str, Path]): Path to audio file
        """
        self.audio_file = Path(audio_file)
        self.metadata_file = self.audio_file.with_suffix('.json')
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata or create new."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'original_file': str(self.audio_file),
            'processing_history': [],
            'created': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def add_processing_step(self, step_name: str, parameters: Dict, output_file: Optional[str] = None):
        """Add a processing step to the metadata."""
        step = {
            'step_name': step_name,
            'timestamp': datetime.now().isoformat(),
            'parameters': parameters,
            'output_file': output_file
        }
        
        self.metadata['processing_history'].append(step)
        self.save_metadata()
    
    def save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save metadata: {e}")
    
    def get_processing_history(self) -> List[Dict]:
        """Get the processing history."""
        return self.metadata.get('processing_history', [])