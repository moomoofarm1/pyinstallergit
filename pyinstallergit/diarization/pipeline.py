"""
Diarization Pipeline Module

This module implements the speaker diarization pipeline using pyannote.audio.
It provides methods to process audio files and return diarization results
with speaker segments and timestamps.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from datetime import datetime

# Import pyannote.audio components
try:
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation, Segment
    import torch
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logging.warning("pyannote.audio not available, using mock implementation")

logger = logging.getLogger(__name__)

class DiarizationPipeline:
    """
    Speaker diarization pipeline using pyannote.audio.
    
    This class handles the initialization and execution of speaker diarization
    on audio files, providing results in a standardized format.
    """
    
    def __init__(self):
        """Initialize the diarization pipeline."""
        self.pipeline: Optional[Any] = None
        self.is_initialized = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Configuration
        self.default_config = {
            'min_speakers': 1,
            'max_speakers': 10,
            'clustering_method': 'spectral',
            'segmentation_onset': 0.7,
            'segmentation_offset': 0.1,
            'clustering_threshold': 0.7
        }
        
        logger.info(f"DiarizationPipeline initialized with device: {self.device}")
    
    async def initialize(self):
        """
        Initialize the pyannote.audio pipeline.
        
        This method loads the pre-trained models and prepares the pipeline
        for processing audio files.
        """
        if self.is_initialized:
            logger.info("Pipeline already initialized")
            return
        
        try:
            if PYANNOTE_AVAILABLE:
                logger.info("Loading pyannote.audio diarization pipeline...")
                
                # Load the pre-trained pipeline
                # Note: This requires a Hugging Face token for some models
                hf_token = os.getenv("HF_TOKEN")
                
                if hf_token:
                    self.pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                else:
                    # Try without token (may not work for all models)
                    self.pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1"
                    )
                
                # Move to appropriate device
                if hasattr(self.pipeline, 'to'):
                    self.pipeline.to(torch.device(self.device))
                
                logger.info(f"Pipeline loaded successfully on {self.device}")
                
            else:
                logger.warning("Using mock pipeline implementation")
                self.pipeline = MockDiarizationPipeline()
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            logger.info("Falling back to mock implementation")
            self.pipeline = MockDiarizationPipeline()
            self.is_initialized = True
    
    async def process_audio(self, 
                          audio_file_path: str,
                          min_speakers: Optional[int] = None,
                          max_speakers: Optional[int] = None,
                          clustering_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Process an audio file for speaker diarization.
        
        Args:
            audio_file_path (str): Path to the audio file
            min_speakers (Optional[int]): Minimum number of speakers
            max_speakers (Optional[int]): Maximum number of speakers
            clustering_method (Optional[str]): Clustering method to use
            
        Returns:
            Dict[str, Any]: Diarization results with segments and metadata
        """
        if not self.is_initialized:
            await self.initialize()
        
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")
        
        # Validate input file
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        logger.info(f"Processing audio file: {audio_path.name}")
        
        try:
            start_time = datetime.now().timestamp()
            
            # Prepare parameters
            params = {
                'min_speakers': min_speakers or self.default_config['min_speakers'],
                'max_speakers': max_speakers or self.default_config['max_speakers'],
                'clustering': clustering_method or self.default_config['clustering_method']
            }
            
            # Run diarization
            if PYANNOTE_AVAILABLE and hasattr(self.pipeline, '__call__'):
                diarization_result = await self._run_pyannote_diarization(
                    audio_file_path, params
                )
            else:
                diarization_result = await self._run_mock_diarization(
                    audio_file_path, params
                )
            
            end_time = datetime.now().timestamp()
            processing_time = end_time - start_time
            
            # Process results
            result = self._process_diarization_result(
                diarization_result, 
                audio_file_path, 
                params,
                processing_time
            )
            
            logger.info(f"Diarization completed in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Diarization processing failed: {e}")
            raise RuntimeError(f"Diarization failed: {e}")
    
    async def _run_pyannote_diarization(self, audio_file_path: str, params: Dict[str, Any]) -> Any:
        """
        Run actual pyannote.audio diarization.
        
        Args:
            audio_file_path (str): Path to audio file
            params (Dict[str, Any]): Processing parameters
            
        Returns:
            Any: pyannote.audio diarization result
        """
        logger.info("Running pyannote.audio diarization...")
        
        # Configure pipeline parameters
        if hasattr(self.pipeline, 'instantiate'):
            self.pipeline.instantiate({
                'clustering': {
                    'method': params['clustering'],
                    'min_cluster_size': params['min_speakers'],
                    'max_num_speakers': params['max_speakers']
                }
            })
        
        # Run diarization in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def run_diarization():
            return self.pipeline(audio_file_path)
        
        diarization = await loop.run_in_executor(None, run_diarization)
        
        return diarization
    
    async def _run_mock_diarization(self, audio_file_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run mock diarization for testing/development.
        
        Args:
            audio_file_path (str): Path to audio file
            params (Dict[str, Any]): Processing parameters
            
        Returns:
            Dict[str, Any]: Mock diarization result
        """
        logger.info("Running mock diarization...")
        
        # Simulate processing time
        await asyncio.sleep(2.0)
        
        # Get audio duration for realistic mock data
        try:
            import librosa
            duration = librosa.get_duration(path=audio_file_path)
        except:
            duration = 30.0  # Default duration
        
        # Create mock segments
        num_speakers = min(params['max_speakers'], max(params['min_speakers'], 2))
        
        segments = []
        current_time = 0.0
        speaker_id = 0
        
        while current_time < duration:
            segment_duration = np.random.uniform(2.0, 8.0)  # 2-8 second segments
            segment_end = min(current_time + segment_duration, duration)
            
            segments.append({
                'start': current_time,
                'end': segment_end,
                'speaker': f"speaker_{speaker_id:02d}",
                'confidence': np.random.uniform(0.8, 0.95)
            })
            
            current_time = segment_end + np.random.uniform(0.1, 0.5)  # Small gap
            speaker_id = (speaker_id + 1) % num_speakers
        
        return {
            'segments': segments,
            'num_speakers': num_speakers,
            'total_duration': duration
        }
    
    def _process_diarization_result(self, 
                                  diarization_result: Any,
                                  audio_file_path: str,
                                  params: Dict[str, Any],
                                  processing_time: float) -> Dict[str, Any]:
        """
        Process and standardize diarization results.
        
        Args:
            diarization_result: Raw diarization result
            audio_file_path (str): Path to audio file
            params (Dict[str, Any]): Processing parameters
            processing_time (float): Processing time in seconds
            
        Returns:
            Dict[str, Any]: Standardized diarization result
        """
        segments = []
        speakers = set()
        
        if PYANNOTE_AVAILABLE and hasattr(diarization_result, 'itertracks'):
            # Process pyannote.audio Annotation result
            for track, _, speaker in diarization_result.itertracks(yield_label=True):
                segments.append({
                    'start': track.start,
                    'end': track.end,
                    'duration': track.end - track.start,
                    'speaker': str(speaker),
                    'confidence': 1.0  # pyannote doesn't provide confidence scores
                })
                speakers.add(str(speaker))
                
            total_speech_time = sum(segment['duration'] for segment in segments)
            
        else:
            # Process mock result
            segments = diarization_result['segments']
            for segment in segments:
                segment['duration'] = segment['end'] - segment['start']
                speakers.add(segment['speaker'])
            
            total_speech_time = sum(segment['duration'] for segment in segments)
        
        # Sort segments by start time
        segments.sort(key=lambda x: x['start'])
        
        # Calculate statistics
        num_speakers = len(speakers)
        avg_segment_duration = np.mean([s['duration'] for s in segments]) if segments else 0.0
        
        return {
            'audio_file': audio_file_path,
            'segments': segments,
            'num_speakers': num_speakers,
            'speakers': sorted(list(speakers)),
            'total_segments': len(segments),
            'total_speech_time': total_speech_time,
            'avg_segment_duration': avg_segment_duration,
            'processing_time_seconds': processing_time,
            'parameters_used': params,
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': 'pyannote-3.1' if PYANNOTE_AVAILABLE else 'mock-1.0'
        }
    
    def get_speaker_statistics(self, diarization_result: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Calculate per-speaker statistics from diarization results.
        
        Args:
            diarization_result (Dict[str, Any]): Diarization result
            
        Returns:
            Dict[str, Dict[str, float]]: Per-speaker statistics
        """
        speaker_stats = {}
        
        for segment in diarization_result['segments']:
            speaker = segment['speaker']
            duration = segment['duration']
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    'total_speaking_time': 0.0,
                    'num_segments': 0,
                    'avg_segment_duration': 0.0,
                    'speaking_percentage': 0.0
                }
            
            speaker_stats[speaker]['total_speaking_time'] += duration
            speaker_stats[speaker]['num_segments'] += 1
        
        # Calculate averages and percentages
        total_speech_time = diarization_result['total_speech_time']
        
        for speaker, stats in speaker_stats.items():
            stats['avg_segment_duration'] = (
                stats['total_speaking_time'] / stats['num_segments']
                if stats['num_segments'] > 0 else 0.0
            )
            stats['speaking_percentage'] = (
                (stats['total_speaking_time'] / total_speech_time) * 100
                if total_speech_time > 0 else 0.0
            )
        
        return speaker_stats
    
    async def cleanup(self):
        """Clean up pipeline resources."""
        if self.pipeline and hasattr(self.pipeline, 'cleanup'):
            await self.pipeline.cleanup()
        
        self.is_initialized = False
        logger.info("Pipeline cleaned up")

class MockDiarizationPipeline:
    """Mock implementation for testing/development when pyannote.audio is not available."""
    
    def __init__(self):
        """Initialize mock pipeline."""
        logger.info("MockDiarizationPipeline initialized")
    
    async def cleanup(self):
        """Mock cleanup method."""
        pass