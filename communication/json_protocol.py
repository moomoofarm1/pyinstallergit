"""
JSON Communication Protocol Module

This module defines the JSON-based communication protocol used between
the GUI application and the various server components (diarization and transcription).

The protocol provides standardized message formats for:
- Server status queries
- Processing requests
- Result notifications
- Error handling
- Progress updates
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import uuid
import queue  # Used for thread-safe messaging

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Enumeration of message types in the communication protocol."""
    
    # Status messages
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"
    
    # Processing messages
    PROCESS_REQUEST = "process_request"
    PROCESS_RESPONSE = "process_response"
    
    # Progress messages
    PROGRESS_UPDATE = "progress_update"
    
    # Error messages
    ERROR_RESPONSE = "error_response"
    
    # Server control messages
    SERVER_START = "server_start"
    SERVER_STOP = "server_stop"
    SERVER_RESTART = "server_restart"
    
    # Data messages
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"

class ProcessingStatus(Enum):
    """Enumeration of processing status values."""
    
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Message:
    """Base message class for all communication."""
    
    message_type: MessageType
    message_id: str
    timestamp: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        """Ensure message_type is an enum value."""
        if isinstance(self.message_type, str):
            self.message_type = MessageType(self.message_type)

@dataclass
class ProcessingRequest:
    """Request for audio processing (diarization or transcription)."""
    
    audio_file_path: str
    processing_type: str  # "diarization" or "transcription"
    parameters: Dict[str, Any]
    output_directory: Optional[str] = None
    priority: int = 1
    
@dataclass
class ProcessingResult:
    """Result of audio processing operation."""
    
    request_id: str
    processing_type: str
    status: ProcessingStatus
    output_files: List[str]
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None

@dataclass
class ServerStatus:
    """Status information for a server component."""
    
    server_type: str  # "diarization" or "transcription"
    status: str  # "running", "stopped", "error"
    port: int
    pid: Optional[int] = None
    uptime_seconds: Optional[float] = None
    active_jobs: int = 0
    total_jobs_processed: int = 0

class JsonProtocol:
    """
    JSON communication protocol handler.
    
    This class provides methods to create, serialize, deserialize, and validate
    JSON messages according to the ALF communication protocol.
    """
    
    def __init__(self):
        """Initialize the JSON protocol handler."""
        self.protocol_version = "1.0"
        logger.info(f"JsonProtocol initialized (version {self.protocol_version})")
    
    def create_message(self, 
                      message_type: MessageType, 
                      payload: Dict[str, Any],
                      correlation_id: Optional[str] = None) -> Message:
        """
        Create a new message with the given type and payload.
        
        Args:
            message_type (MessageType): Type of message to create
            payload (Dict[str, Any]): Message payload data
            correlation_id (Optional[str]): ID to correlate with previous message
            
        Returns:
            Message: Created message object
        """
        message = Message(
            message_type=message_type,
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            payload=payload,
            correlation_id=correlation_id
        )
        
        logger.debug(f"Created message: {message_type.value} (ID: {message.message_id})")
        return message
    
    def serialize_message(self, message: Message) -> str:
        """
        Serialize a message to JSON string.
        
        Args:
            message (Message): Message to serialize
            
        Returns:
            str: JSON string representation
        """
        try:
            # Convert message to dictionary
            message_dict = asdict(message)
            
            # Convert enum to string
            if isinstance(message_dict['message_type'], MessageType):
                message_dict['message_type'] = message_dict['message_type'].value
            elif hasattr(message_dict['message_type'], 'value'):
                message_dict['message_type'] = message_dict['message_type'].value
            
            # Add protocol version
            message_dict['protocol_version'] = self.protocol_version
            
            json_str = json.dumps(message_dict, indent=2, ensure_ascii=False)
            logger.debug(f"Serialized message ID: {message.message_id}")
            return json_str
            
        except Exception as e:
            logger.error(f"Message serialization failed: {e}")
            raise ValueError(f"Cannot serialize message: {e}")
    
    def deserialize_message(self, json_str: str) -> Message:
        """
        Deserialize a JSON string to message object.
        
        Args:
            json_str (str): JSON string to deserialize
            
        Returns:
            Message: Deserialized message object
        """
        try:
            message_dict = json.loads(json_str)
            
            # Validate protocol version
            protocol_version = message_dict.get('protocol_version', '1.0')
            if protocol_version != self.protocol_version:
                logger.warning(f"Protocol version mismatch: expected {self.protocol_version}, got {protocol_version}")
            
            # Remove protocol version from dict (not part of Message dataclass)
            message_dict.pop('protocol_version', None)
            
            # Convert string to enum
            if 'message_type' in message_dict:
                message_dict['message_type'] = MessageType(message_dict['message_type'])
            
            message = Message(**message_dict)
            logger.debug(f"Deserialized message ID: {message.message_id}")
            return message
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Message deserialization failed: {e}")
            raise ValueError(f"Invalid message format: {e}")
    
    def create_status_request(self, server_type: str) -> Message:
        """
        Create a status request message.
        
        Args:
            server_type (str): Type of server to query ("diarization" or "transcription")
            
        Returns:
            Message: Status request message
        """
        payload = {
            'server_type': server_type,
            'requested_fields': ['status', 'port', 'pid', 'uptime_seconds', 'active_jobs']
        }
        
        return self.create_message(MessageType.STATUS_REQUEST, payload)
    
    def create_status_response(self, server_status: ServerStatus, request_id: str) -> Message:
        """
        Create a status response message.
        
        Args:
            server_status (ServerStatus): Server status information
            request_id (str): ID of the original request
            
        Returns:
            Message: Status response message
        """
        payload = asdict(server_status)
        
        return self.create_message(
            MessageType.STATUS_RESPONSE, 
            payload, 
            correlation_id=request_id
        )
    
    def create_processing_request(self, processing_request: ProcessingRequest) -> Message:
        """
        Create a processing request message.
        
        Args:
            processing_request (ProcessingRequest): Processing request details
            
        Returns:
            Message: Processing request message
        """
        payload = asdict(processing_request)
        
        return self.create_message(MessageType.PROCESS_REQUEST, payload)
    
    def create_processing_response(self, processing_result: ProcessingResult, request_id: str) -> Message:
        """
        Create a processing response message.
        
        Args:
            processing_result (ProcessingResult): Processing result details
            request_id (str): ID of the original request
            
        Returns:
            Message: Processing response message
        """
        payload = asdict(processing_result)
        
        # Convert enum to string
        if isinstance(payload['status'], ProcessingStatus):
            payload['status'] = payload['status'].value
        
        return self.create_message(
            MessageType.PROCESS_RESPONSE, 
            payload, 
            correlation_id=request_id
        )
    
    def create_progress_update(self, 
                             request_id: str,
                             progress_percent: float,
                             status_message: str,
                             details: Optional[Dict[str, Any]] = None) -> Message:
        """
        Create a progress update message.
        
        Args:
            request_id (str): ID of the request being processed
            progress_percent (float): Progress percentage (0-100)
            status_message (str): Human-readable status message
            details (Optional[Dict[str, Any]]): Additional progress details
            
        Returns:
            Message: Progress update message
        """
        payload = {
            'request_id': request_id,
            'progress_percent': max(0, min(100, progress_percent)),
            'status_message': status_message,
            'details': details or {}
        }
        
        return self.create_message(
            MessageType.PROGRESS_UPDATE, 
            payload, 
            correlation_id=request_id
        )
    
    def create_error_response(self, 
                            error_code: str,
                            error_message: str,
                            request_id: Optional[str] = None,
                            details: Optional[Dict[str, Any]] = None) -> Message:
        """
        Create an error response message.
        
        Args:
            error_code (str): Error code identifier
            error_message (str): Human-readable error message
            request_id (Optional[str]): ID of the request that caused the error
            details (Optional[Dict[str, Any]]): Additional error details
            
        Returns:
            Message: Error response message
        """
        payload = {
            'error_code': error_code,
            'error_message': error_message,
            'request_id': request_id,
            'details': details or {}
        }
        
        return self.create_message(
            MessageType.ERROR_RESPONSE, 
            payload, 
            correlation_id=request_id
        )
    
    def validate_message(self, message: Message) -> Dict[str, Any]:
        """
        Validate a message for correctness and completeness.
        
        Args:
            message (Message): Message to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check required fields
            if not message.message_id:
                validation['errors'].append("Missing message_id")
            
            if not message.timestamp:
                validation['errors'].append("Missing timestamp")
            
            if not isinstance(message.message_type, MessageType):
                validation['errors'].append("Invalid message_type")
            
            if not isinstance(message.payload, dict):
                validation['errors'].append("Payload must be a dictionary")
            
            # Type-specific validation
            if message.message_type == MessageType.PROCESS_REQUEST:
                self._validate_processing_request(message.payload, validation)
            elif message.message_type == MessageType.STATUS_REQUEST:
                self._validate_status_request(message.payload, validation)
            
            # Set overall validity
            validation['valid'] = len(validation['errors']) == 0
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"Validation exception: {e}")
        
        return validation
    
    def _validate_processing_request(self, payload: Dict[str, Any], validation: Dict[str, Any]):
        """Validate processing request payload."""
        required_fields = ['audio_file_path', 'processing_type', 'parameters']
        
        for field in required_fields:
            if field not in payload:
                validation['errors'].append(f"Missing required field: {field}")
        
        # Validate processing type
        valid_types = ['diarization', 'transcription']
        if payload.get('processing_type') not in valid_types:
            validation['errors'].append(f"Invalid processing_type. Must be one of: {valid_types}")
        
        # Validate file path exists (if we can check)
        import os
        audio_file = payload.get('audio_file_path')
        if audio_file and not os.path.exists(audio_file):
            validation['warnings'].append(f"Audio file may not exist: {audio_file}")
    
    def _validate_status_request(self, payload: Dict[str, Any], validation: Dict[str, Any]):
        """Validate status request payload."""
        if 'server_type' not in payload:
            validation['errors'].append("Missing required field: server_type")
        
        valid_server_types = ['diarization', 'transcription']
        if payload.get('server_type') not in valid_server_types:
            validation['errors'].append(f"Invalid server_type. Must be one of: {valid_server_types}")
    
    def create_rttm_data_message(self, rttm_content: str, audio_file: str) -> Message:
        """
        Create a message containing RTTM diarization data.
        
        Args:
            rttm_content (str): RTTM file content
            audio_file (str): Path to the associated audio file
            
        Returns:
            Message: Data message with RTTM content
        """
        payload = {
            'data_type': 'rttm',
            'audio_file': audio_file,
            'rttm_content': rttm_content,
            'format_version': '2.1'  # RTTM format version
        }
        
        return self.create_message(MessageType.DATA_RESPONSE, payload)
    
    def create_transcription_data_message(self, transcription_text: str, 
                                        segments: List[Dict[str, Any]],
                                        audio_file: str) -> Message:
        """
        Create a message containing transcription data.
        
        Args:
            transcription_text (str): Full transcription text
            segments (List[Dict[str, Any]]): List of transcription segments with timestamps
            audio_file (str): Path to the associated audio file
            
        Returns:
            Message: Data message with transcription content
        """
        payload = {
            'data_type': 'transcription',
            'audio_file': audio_file,
            'transcription_text': transcription_text,
            'segments': segments,
            'total_segments': len(segments)
        }
        
        return self.create_message(MessageType.DATA_RESPONSE, payload)
    
    def log_message(self, message: Message, direction: str = "unknown"):
        """
        Log a message for debugging purposes.
        
        Args:
            message (Message): Message to log
            direction (str): Direction of message flow ("sent", "received", etc.)
        """
        logger.info(f"Message {direction}: {message.message_type.value} "
                   f"(ID: {message.message_id[:8]}...)")
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Message details: {self.serialize_message(message)}")

class MessageQueue:
    """
    Simple message queue for handling asynchronous communication.
    """
    
    def __init__(self, maxsize: int = 100):
        """Initialize message queue with maximum size."""
        import queue
        self.queue = queue.Queue(maxsize=maxsize)
        self.logger = logging.getLogger(f"{__name__}.MessageQueue")
    
    def put_message(self, message: Message, timeout: Optional[float] = None):
        """Put a message in the queue."""
        try:
            self.queue.put(message, timeout=timeout)
            self.logger.debug(f"Queued message: {message.message_type.value}")
        except queue.Full:
            self.logger.error("Message queue is full, dropping message")
            raise
    
    def get_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Get a message from the queue."""
        try:
            message = self.queue.get(timeout=timeout)
            self.logger.debug(f"Retrieved message: {message.message_type.value}")
            return message
        except queue.Empty:
            return None
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
    
    def clear_queue(self):
        """Clear all messages from the queue."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        self.logger.info("Message queue cleared")