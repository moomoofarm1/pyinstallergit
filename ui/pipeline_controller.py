"""
Pipeline Controller Module

This module manages the execution of audio processing pipelines including
diarization and transcription workflows. It coordinates between the UI,
server management, and processing components.
"""

import logging
import webbrowser
from typing import Optional, Dict, Any, List
import threading
import time
from pathlib import Path

from communication.server_manager import ServerManager, ServerType
from communication.json_protocol import JsonProtocol, ProcessingRequest, MessageType

logger = logging.getLogger(__name__)

class PipelineController:
    """
    Controller for managing audio processing pipelines.
    
    This class coordinates the execution of diarization and transcription
    pipelines, handles browser launching for Label Studio interfaces,
    and manages communication between components.
    """
    
    def __init__(self, server_manager: ServerManager, json_protocol: JsonProtocol):
        """
        Initialize the pipeline controller.
        
        Args:
            server_manager (ServerManager): Server management instance
            json_protocol (JsonProtocol): JSON communication protocol instance
        """
        self.server_manager = server_manager
        self.json_protocol = json_protocol
        
        # Pipeline state tracking
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_counter = 0
        
        logger.info("PipelineController initialized")
    
    def run_diarization_pipeline(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Run the complete diarization pipeline on an audio file.
        
        This method:
        1. Validates the audio file
        2. Ensures the diarization server is running
        3. Submits the processing request
        4. Monitors progress
        5. Returns results
        
        Args:
            audio_file_path (str): Path to the preprocessed audio file
            
        Returns:
            Dict[str, Any]: Processing results and metadata
        """
        logger.info(f"Starting diarization pipeline for: {audio_file_path}")
        
        try:
            # Validate input file
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Ensure diarization server is running
            if not self.server_manager.is_diarization_running():
                logger.info("Starting diarization server...")
                if not self.server_manager.start_diarization_server():
                    raise RuntimeError("Failed to start diarization server")
            
            # Create processing request
            job_id = self._generate_job_id("diarization")
            
            processing_request = ProcessingRequest(
                audio_file_path=audio_file_path,
                processing_type="diarization",
                parameters={
                    "min_speakers": 1,
                    "max_speakers": 10,
                    "clustering_method": "spectral",
                    "output_format": "rttm"
                },
                output_directory=str(Path("outputs") / "diarization")
            )
            
            # Submit processing request
            result = self._submit_processing_request(job_id, processing_request, ServerType.DIARIZATION)
            
            logger.info(f"Diarization pipeline completed for job: {job_id}")
            return result
            
        except FileNotFoundError:
            # Preserve FileNotFoundError for caller to handle
            logger.error(f"Audio file not found: {audio_file_path}")
            raise
        except Exception as e:
            logger.error(f"Diarization pipeline failed: {e}")
            raise RuntimeError(f"Diarization pipeline error: {e}")
    
    def run_transcription_pipeline(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Run the complete transcription pipeline on an audio file.
        
        This method:
        1. Validates the audio file
        2. Ensures the transcription server is running
        3. Submits the processing request
        4. Monitors progress
        5. Returns results
        
        Args:
            audio_file_path (str): Path to the preprocessed audio file
            
        Returns:
            Dict[str, Any]: Processing results and metadata
        """
        logger.info(f"Starting transcription pipeline for: {audio_file_path}")
        
        try:
            # Validate input file
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Ensure transcription server is running
            if not self.server_manager.is_transcription_running():
                logger.info("Starting transcription server...")
                if not self.server_manager.start_transcription_server():
                    raise RuntimeError("Failed to start transcription server")
            
            # Create processing request
            job_id = self._generate_job_id("transcription")
            
            processing_request = ProcessingRequest(
                audio_file_path=audio_file_path,
                processing_type="transcription",
                parameters={
                    "model_name": "nvidia/stt_en_conformer_ctc_large",
                    "language": "en",
                    "punctuation": True,
                    "output_format": "segments"
                },
                output_directory=str(Path("outputs") / "transcription")
            )
            
            # Submit processing request
            result = self._submit_processing_request(job_id, processing_request, ServerType.TRANSCRIPTION)
            
            logger.info(f"Transcription pipeline completed for job: {job_id}")
            return result
            
        except Exception as e:
            logger.error(f"Transcription pipeline failed: {e}")
            raise RuntimeError(f"Transcription pipeline error: {e}")
    
    def _generate_job_id(self, pipeline_type: str) -> str:
        """Generate a unique job ID for tracking."""
        self.job_counter += 1
        return f"{pipeline_type}_{int(time.time())}_{self.job_counter}"
    
    def _submit_processing_request(self, job_id: str, 
                                 processing_request: ProcessingRequest,
                                 server_type: ServerType) -> Dict[str, Any]:
        """
        Submit a processing request to the appropriate server.
        
        Args:
            job_id (str): Unique job identifier
            processing_request (ProcessingRequest): Processing request details
            server_type (ServerType): Target server type
            
        Returns:
            Dict[str, Any]: Processing results
        """
        # Track the job
        self.active_jobs[job_id] = {
            'server_type': server_type,
            'request': processing_request,
            'status': 'submitted',
            'start_time': time.time(),
            'progress': 0.0
        }
        
        try:
            # Create JSON message
            message = self.json_protocol.create_processing_request(processing_request)
            
            # For now, simulate processing since we don't have the actual servers implemented yet
            # In a real implementation, this would send the message to the server
            result = self._simulate_processing(job_id, processing_request, server_type)
            
            # Update job status
            self.active_jobs[job_id]['status'] = 'completed'
            self.active_jobs[job_id]['end_time'] = time.time()
            self.active_jobs[job_id]['result'] = result
            
            return result
            
        except Exception as e:
            self.active_jobs[job_id]['status'] = 'failed'
            self.active_jobs[job_id]['error'] = str(e)
            raise
    
    def _simulate_processing(self, job_id: str, 
                           processing_request: ProcessingRequest,
                           server_type: ServerType) -> Dict[str, Any]:
        """
        Simulate processing for development/testing purposes.
        
        This method will be replaced with actual server communication
        once the diarization and transcription servers are implemented.
        """
        logger.info(f"Simulating {processing_request.processing_type} processing for job: {job_id}")
        
        # Simulate processing time
        processing_time = 5.0  # 5 seconds simulation
        steps = 10
        step_time = processing_time / steps
        
        for i in range(steps):
            time.sleep(step_time)
            progress = ((i + 1) / steps) * 100
            self.active_jobs[job_id]['progress'] = progress
            logger.debug(f"Job {job_id} progress: {progress:.1f}%")
        
        # Create mock results based on processing type
        if processing_request.processing_type == "diarization":
            return self._create_mock_diarization_result(processing_request)
        else:
            return self._create_mock_transcription_result(processing_request)
    
    def _create_mock_diarization_result(self, processing_request: ProcessingRequest) -> Dict[str, Any]:
        """Create mock diarization results."""
        output_dir = Path(processing_request.output_directory or "outputs/diarization")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_file = Path(processing_request.audio_file_path)
        rttm_file = output_dir / f"{audio_file.stem}.rttm"
        
        # Create mock RTTM content
        mock_rttm_content = """SPEAKER {audio_stem} 1 0.000 2.500 <NA> <NA> speaker_00 <NA> <NA>
SPEAKER {audio_stem} 1 2.500 3.000 <NA> <NA> speaker_01 <NA> <NA>
SPEAKER {audio_stem} 1 5.500 4.200 <NA> <NA> speaker_00 <NA> <NA>
SPEAKER {audio_stem} 1 9.700 2.800 <NA> <NA> speaker_01 <NA> <NA>""".format(
            audio_stem=audio_file.stem
        )
        
        # Write RTTM file
        with open(rttm_file, 'w') as f:
            f.write(mock_rttm_content)
        
        return {
            'job_type': 'diarization',
            'status': 'completed',
            'output_files': [str(rttm_file)],
            'num_speakers': 2,
            'total_speech_time': 12.5,
            'processing_time_seconds': 5.0,
            'parameters_used': processing_request.parameters
        }
    
    def _create_mock_transcription_result(self, processing_request: ProcessingRequest) -> Dict[str, Any]:
        """Create mock transcription results."""
        output_dir = Path(processing_request.output_directory or "outputs/transcription")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_file = Path(processing_request.audio_file_path)
        transcript_file = output_dir / f"{audio_file.stem}.txt"
        segments_file = output_dir / f"{audio_file.stem}_segments.json"
        
        # Create mock transcription content
        mock_transcript = "Hello this is a sample transcription of the audio file. The speaker discusses various topics including technology and artificial intelligence."
        
        mock_segments = [
            {
                "start_time": 0.0,
                "end_time": 3.2,
                "text": "Hello this is a sample transcription of the audio file.",
                "confidence": 0.95
            },
            {
                "start_time": 3.5,
                "end_time": 7.8,
                "text": "The speaker discusses various topics including technology",
                "confidence": 0.92
            },
            {
                "start_time": 8.1,
                "end_time": 11.4,
                "text": "and artificial intelligence.",
                "confidence": 0.94
            }
        ]
        
        # Write transcript file
        with open(transcript_file, 'w') as f:
            f.write(mock_transcript)
        
        # Write segments file
        import json
        with open(segments_file, 'w') as f:
            json.dump(mock_segments, f, indent=2)
        
        return {
            'job_type': 'transcription',
            'status': 'completed',
            'output_files': [str(transcript_file), str(segments_file)],
            'full_transcript': mock_transcript,
            'segments': mock_segments,
            'word_count': len(mock_transcript.split()),
            'processing_time_seconds': 5.0,
            'parameters_used': processing_request.parameters
        }
    
    def open_diarization_browser(self):
        """
        Open Label Studio browser for diarization workflow.
        
        This opens a web browser pointing to a Label Studio instance
        configured for speaker diarization annotation and verification.
        """
        try:
            # Label Studio should be automatically running when diarization server starts
            diarization_url = "http://localhost:8080"
            
            logger.info(f"Opening diarization browser: {diarization_url}")
            
            # Check if we can reach the URL first
            import requests
            try:
                response = requests.get(diarization_url, timeout=5)
                if response.status_code == 200:
                    webbrowser.open(diarization_url)
                    logger.info("Label Studio diarization browser opened successfully")
                else:
                    # Label Studio not responding properly
                    logger.warning(f"Label Studio responded with status code: {response.status_code}")
                    webbrowser.open(diarization_url)  # Try opening anyway
            except requests.RequestException as e:
                # Label Studio not available, try opening anyway or show message
                logger.warning(f"Cannot reach Label Studio at {diarization_url}: {e}")
                logger.info("Attempting to open browser anyway - Label Studio may still be starting up")
                webbrowser.open(diarization_url)
                
        except Exception as e:
            logger.error(f"Failed to open diarization browser: {e}")
            raise RuntimeError(f"Cannot open diarization browser: {e}")
    
    def open_transcription_browser(self):
        """
        Open Label Studio browser for transcription workflow.
        
        This opens a web browser pointing to a Label Studio instance
        configured for speech transcription annotation and correction.
        """
        try:
            # For now, open a placeholder URL
            # In the actual implementation, this would be the Label Studio instance
            # configured with the transcription project template
            
            transcription_url = "http://localhost:8080/projects/transcription"
            
            logger.info(f"Opening transcription browser: {transcription_url}")
            
            # Check if we can reach the URL first
            import requests
            try:
                response = requests.get("http://localhost:8080", timeout=2)
                if response.status_code == 200:
                    webbrowser.open(transcription_url)
                else:
                    # Label Studio not running, open setup page
                    self._open_label_studio_setup("transcription")
            except requests.RequestException:
                # Label Studio not available, show setup instructions
                self._open_label_studio_setup("transcription")
                
        except Exception as e:
            logger.error(f"Failed to open transcription browser: {e}")
            raise RuntimeError(f"Cannot open transcription browser: {e}")
    
    def _open_label_studio_setup(self, workflow_type: str):
        """
        Open Label Studio setup instructions.
        
        Args:
            workflow_type (str): Type of workflow ("diarization" or "transcription")
        """
        # Create a simple HTML page with setup instructions
        setup_html = self._create_setup_page(workflow_type)
        
        # Write to temporary file and open
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(setup_html)
            temp_file = f.name
        
        webbrowser.open(f"file://{temp_file}")
        logger.info(f"Opened {workflow_type} setup instructions")
    
    def _create_setup_page(self, workflow_type: str) -> str:
        """Create HTML setup instructions page."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ALF - {workflow_type.title()} Setup</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; }}
                .step {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .command {{ background: #2c3e50; color: white; padding: 10px; border-radius: 3px; font-family: monospace; }}
                .note {{ background: #f39c12; color: white; padding: 10px; border-radius: 3px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>ALF - {workflow_type.title()} Setup</h1>
                
                <div class="note">
                    <strong>Note:</strong> Label Studio is not currently running. Please follow these steps to set up the {workflow_type} workflow.
                </div>
                
                <h2>Setup Steps</h2>
                
                <div class="step">
                    <h3>1. Install Label Studio</h3>
                    <div class="command">pip install label-studio</div>
                </div>
                
                <div class="step">
                    <h3>2. Start Label Studio</h3>
                    <div class="command">label-studio start</div>
                </div>
                
                <div class="step">
                    <h3>3. Create a new project</h3>
                    <p>1. Go to <a href="http://localhost:8080" target="_blank">http://localhost:8080</a></p>
                    <p>2. Create a new project</p>
                    <p>3. Choose "{workflow_type.title()}" template</p>
                    <p>4. Configure the ML backend URL: <code>http://localhost:909{'1' if workflow_type == 'diarization' else '2'}</code></p>
                </div>
                
                <div class="step">
                    <h3>4. Import your data</h3>
                    <p>Upload your preprocessed audio files to the Label Studio project</p>
                </div>
                
                <h2>Next Steps</h2>
                <p>After completing the setup:</p>
                <ul>
                    <li>Return to ALF application</li>
                    <li>Ensure the {workflow_type} server is running</li>
                    <li>Click "Open Label Studio ({workflow_type.title()})" again</li>
                </ul>
            </div>
        </body>
        </html>
        """
    
    def get_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active jobs."""
        return self.active_jobs.copy()
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific job.
        
        Args:
            job_id (str): Job identifier
            
        Returns:
            Optional[Dict[str, Any]]: Job status information or None if not found
        """
        return self.active_jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id (str): Job identifier
            
        Returns:
            bool: True if job was cancelled successfully
        """
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            logger.warning(f"Job not found for cancellation: {job_id}")
            return False
        
        if job_info['status'] in ['completed', 'failed', 'cancelled']:
            logger.info(f"Job {job_id} is already finished, cannot cancel")
            return False
        
        try:
            # Update job status
            job_info['status'] = 'cancelled'
            job_info['end_time'] = time.time()
            
            logger.info(f"Job {job_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """
        Clean up old completed jobs to free memory.
        
        Args:
            max_age_hours (int): Maximum age in hours for keeping completed jobs
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        jobs_to_remove = []
        for job_id, job_info in self.active_jobs.items():
            if job_info['status'] in ['completed', 'failed', 'cancelled']:
                job_age = current_time - job_info.get('end_time', job_info['start_time'])
                if job_age > max_age_seconds:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            logger.info(f"Cleaned up old job: {job_id}")
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")