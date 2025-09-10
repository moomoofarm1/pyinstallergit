"""
Unit tests for JSON communication protocol.

These tests validate the JSON-based communication system including
message creation, serialization, deserialization, and validation.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch

from communication.json_protocol import (
    JsonProtocol, 
    MessageType, 
    ProcessingStatus,
    Message,
    ProcessingRequest,
    ProcessingResult,
    ServerStatus,
    MessageQueue
)

class TestJsonProtocol:
    """Test cases for JsonProtocol class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.protocol = JsonProtocol()
    
    def test_protocol_initialization(self):
        """Test JsonProtocol initialization."""
        assert self.protocol.protocol_version == "1.0"
    
    def test_create_message(self):
        """Test basic message creation."""
        payload = {"test": "data", "number": 42}
        message = self.protocol.create_message(MessageType.STATUS_REQUEST, payload)
        
        assert message.message_type == MessageType.STATUS_REQUEST
        assert message.payload == payload
        assert message.message_id is not None
        assert message.timestamp is not None
        assert len(message.message_id) > 0
    
    def test_create_message_with_correlation(self):
        """Test message creation with correlation ID."""
        payload = {"response": "data"}
        correlation_id = "test-correlation-123"
        
        message = self.protocol.create_message(
            MessageType.STATUS_RESPONSE, 
            payload,
            correlation_id=correlation_id
        )
        
        assert message.correlation_id == correlation_id
    
    def test_serialize_message(self):
        """Test message serialization to JSON."""
        payload = {"test_key": "test_value", "number": 123}
        message = self.protocol.create_message(MessageType.PROCESS_REQUEST, payload)
        
        json_str = self.protocol.serialize_message(message)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        
        assert parsed['message_type'] == 'process_request'
        assert parsed['payload'] == payload
        assert parsed['message_id'] == message.message_id
        assert parsed['protocol_version'] == '1.0'
    
    def test_deserialize_message(self):
        """Test message deserialization from JSON."""
        # Create and serialize a message
        original_payload = {"original": "data", "value": 456}
        original_message = self.protocol.create_message(MessageType.ERROR_RESPONSE, original_payload)
        json_str = self.protocol.serialize_message(original_message)
        
        # Deserialize it
        deserialized = self.protocol.deserialize_message(json_str)
        
        assert deserialized.message_type == MessageType.ERROR_RESPONSE
        assert deserialized.payload == original_payload
        assert deserialized.message_id == original_message.message_id
        assert deserialized.timestamp == original_message.timestamp
    
    def test_deserialize_invalid_json(self):
        """Test deserialization with invalid JSON."""
        invalid_json = "{ invalid json }"
        
        with pytest.raises(ValueError, match="Invalid JSON format"):
            self.protocol.deserialize_message(invalid_json)
    
    def test_deserialize_invalid_message_format(self):
        """Test deserialization with invalid message format."""
        # Missing required fields
        incomplete_json = json.dumps({
            "message_type": "status_request",
            "payload": {}
            # Missing message_id and timestamp
        })
        
        with pytest.raises(ValueError, match="Invalid message format"):
            self.protocol.deserialize_message(incomplete_json)
    
    def test_create_status_request(self):
        """Test creation of status request message."""
        message = self.protocol.create_status_request("diarization")
        
        assert message.message_type == MessageType.STATUS_REQUEST
        assert message.payload['server_type'] == 'diarization'
        assert 'requested_fields' in message.payload
    
    def test_create_status_response(self):
        """Test creation of status response message."""
        server_status = ServerStatus(
            server_type="transcription",
            status="running",
            port=9092,
            pid=12345,
            uptime_seconds=3600.0,
            active_jobs=2
        )
        request_id = "test-request-123"
        
        message = self.protocol.create_status_response(server_status, request_id)
        
        assert message.message_type == MessageType.STATUS_RESPONSE
        assert message.correlation_id == request_id
        assert message.payload['server_type'] == 'transcription'
        assert message.payload['status'] == 'running'
        assert message.payload['port'] == 9092
        assert message.payload['pid'] == 12345
    
    def test_create_processing_request(self):
        """Test creation of processing request message."""
        processing_request = ProcessingRequest(
            audio_file_path="/path/to/audio.wav",
            processing_type="diarization",
            parameters={"min_speakers": 2, "max_speakers": 5},
            output_directory="/path/to/output"
        )
        
        message = self.protocol.create_processing_request(processing_request)
        
        assert message.message_type == MessageType.PROCESS_REQUEST
        assert message.payload['audio_file_path'] == '/path/to/audio.wav'
        assert message.payload['processing_type'] == 'diarization'
        assert message.payload['parameters']['min_speakers'] == 2
    
    def test_create_processing_response(self):
        """Test creation of processing response message."""
        processing_result = ProcessingResult(
            request_id="test-job-456",
            processing_type="transcription",
            status=ProcessingStatus.COMPLETED,
            output_files=["/path/to/result.txt"],
            metadata={"duration": 120.5},
            processing_time_seconds=45.2
        )
        request_id = "original-request-123"
        
        message = self.protocol.create_processing_response(processing_result, request_id)
        
        assert message.message_type == MessageType.PROCESS_RESPONSE
        assert message.correlation_id == request_id
        assert message.payload['status'] == 'completed'  # Enum converted to string
        assert message.payload['output_files'] == ['/path/to/result.txt']
        assert message.payload['processing_time_seconds'] == 45.2
    
    def test_create_progress_update(self):
        """Test creation of progress update message."""
        request_id = "job-789"
        message = self.protocol.create_progress_update(
            request_id=request_id,
            progress_percent=65.5,
            status_message="Processing audio segments...",
            details={"current_segment": 3, "total_segments": 5}
        )
        
        assert message.message_type == MessageType.PROGRESS_UPDATE
        assert message.correlation_id == request_id
        assert message.payload['progress_percent'] == 65.5
        assert message.payload['status_message'] == "Processing audio segments..."
        assert message.payload['details']['current_segment'] == 3
    
    def test_progress_update_bounds_checking(self):
        """Test that progress percentage is bounded between 0-100."""
        # Test over 100%
        message1 = self.protocol.create_progress_update("job1", 150.0, "Over 100%")
        assert message1.payload['progress_percent'] == 100.0
        
        # Test under 0%
        message2 = self.protocol.create_progress_update("job2", -10.0, "Under 0%")
        assert message2.payload['progress_percent'] == 0.0
    
    def test_create_error_response(self):
        """Test creation of error response message."""
        message = self.protocol.create_error_response(
            error_code="PROCESSING_FAILED",
            error_message="Audio file is corrupted",
            request_id="failed-job-456",
            details={"file_path": "/path/to/bad/file.wav", "error_type": "corruption"}
        )
        
        assert message.message_type == MessageType.ERROR_RESPONSE
        assert message.correlation_id == "failed-job-456"
        assert message.payload['error_code'] == "PROCESSING_FAILED"
        assert message.payload['error_message'] == "Audio file is corrupted"
        assert message.payload['details']['error_type'] == "corruption"
    
    def test_validate_message_valid(self):
        """Test validation of valid message."""
        message = self.protocol.create_message(
            MessageType.STATUS_REQUEST,
            {"server_type": "diarization"}
        )
        
        validation = self.protocol.validate_message(message)
        
        assert validation['valid'] is True
        assert len(validation['errors']) == 0
    
    def test_validate_message_missing_fields(self):
        """Test validation of message with missing required fields."""
        # Create message with missing fields
        message = Message(
            message_type=MessageType.PROCESS_REQUEST,
            message_id="",  # Empty ID
            timestamp="",   # Empty timestamp
            payload={}      # Empty payload
        )
        
        validation = self.protocol.validate_message(message)
        
        assert validation['valid'] is False
        assert len(validation['errors']) > 0
        assert any("message_id" in error for error in validation['errors'])
        assert any("timestamp" in error for error in validation['errors'])
    
    def test_validate_processing_request(self):
        """Test validation of processing request payload."""
        # Valid processing request
        valid_message = self.protocol.create_processing_request(ProcessingRequest(
            audio_file_path="/path/to/audio.wav",
            processing_type="diarization",
            parameters={}
        ))
        
        validation = self.protocol.validate_message(valid_message)
        assert validation['valid'] is True
        
        # Invalid processing request (missing required fields)
        invalid_message = self.protocol.create_message(
            MessageType.PROCESS_REQUEST,
            {"processing_type": "invalid_type"}  # Missing audio_file_path, invalid type
        )
        
        validation = self.protocol.validate_message(invalid_message)
        assert validation['valid'] is False
        assert len(validation['errors']) > 0
    
    def test_create_rttm_data_message(self):
        """Test creation of RTTM data message."""
        rttm_content = "SPEAKER audio_file 1 0.000 5.500 <NA> <NA> speaker_00 <NA> <NA>"
        audio_file = "/path/to/audio.wav"
        
        message = self.protocol.create_rttm_data_message(rttm_content, audio_file)
        
        assert message.message_type == MessageType.DATA_RESPONSE
        assert message.payload['data_type'] == 'rttm'
        assert message.payload['rttm_content'] == rttm_content
        assert message.payload['audio_file'] == audio_file
    
    def test_create_transcription_data_message(self):
        """Test creation of transcription data message."""
        transcript = "This is a test transcription"
        segments = [
            {"start": 0.0, "end": 2.5, "text": "This is a", "confidence": 0.95},
            {"start": 2.5, "end": 5.0, "text": "test transcription", "confidence": 0.92}
        ]
        audio_file = "/path/to/audio.wav"
        
        message = self.protocol.create_transcription_data_message(
            transcript, segments, audio_file
        )
        
        assert message.message_type == MessageType.DATA_RESPONSE
        assert message.payload['data_type'] == 'transcription'
        assert message.payload['transcription_text'] == transcript
        assert message.payload['segments'] == segments
        assert message.payload['total_segments'] == 2

class TestMessageQueue:
    """Test cases for MessageQueue class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.queue = MessageQueue(maxsize=3)
        self.protocol = JsonProtocol()
    
    def test_queue_initialization(self):
        """Test MessageQueue initialization."""
        assert self.queue.get_queue_size() == 0
    
    def test_put_and_get_message(self):
        """Test putting and getting messages from queue."""
        # Create test message
        message = self.protocol.create_message(
            MessageType.STATUS_REQUEST,
            {"server_type": "diarization"}
        )
        
        # Put message in queue
        self.queue.put_message(message)
        assert self.queue.get_queue_size() == 1
        
        # Get message from queue
        retrieved = self.queue.get_message()
        assert retrieved is not None
        assert retrieved.message_id == message.message_id
        assert self.queue.get_queue_size() == 0
    
    def test_queue_empty(self):
        """Test getting message from empty queue."""
        message = self.queue.get_message(timeout=0.1)
        assert message is None
    
    def test_queue_full(self):
        """Test queue size limit."""
        # Fill the queue to capacity
        for i in range(3):
            message = self.protocol.create_message(
                MessageType.STATUS_REQUEST,
                {"index": i}
            )
            self.queue.put_message(message, timeout=0.1)
        
        assert self.queue.get_queue_size() == 3
        
        # Try to add one more (should raise exception)
        overflow_message = self.protocol.create_message(
            MessageType.STATUS_REQUEST,
            {"overflow": True}
        )
        
        with pytest.raises(Exception):  # queue.Full exception
            self.queue.put_message(overflow_message, timeout=0.1)
    
    def test_clear_queue(self):
        """Test clearing the message queue."""
        # Add some messages
        for i in range(3):
            message = self.protocol.create_message(
                MessageType.STATUS_REQUEST,
                {"index": i}
            )
            self.queue.put_message(message)
        
        assert self.queue.get_queue_size() == 3
        
        # Clear queue
        self.queue.clear_queue()
        assert self.queue.get_queue_size() == 0

class TestMessageTypes:
    """Test cases for message type enums and data classes."""
    
    def test_message_type_enum(self):
        """Test MessageType enum values."""
        assert MessageType.STATUS_REQUEST.value == "status_request"
        assert MessageType.PROCESS_REQUEST.value == "process_request"
        assert MessageType.ERROR_RESPONSE.value == "error_response"
    
    def test_processing_status_enum(self):
        """Test ProcessingStatus enum values."""
        assert ProcessingStatus.IDLE.value == "idle"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
    
    def test_processing_request_dataclass(self):
        """Test ProcessingRequest dataclass."""
        request = ProcessingRequest(
            audio_file_path="/test/path.wav",
            processing_type="diarization",
            parameters={"test": "param"}
        )
        
        assert request.audio_file_path == "/test/path.wav"
        assert request.processing_type == "diarization"
        assert request.parameters == {"test": "param"}
        assert request.priority == 1  # Default value
    
    def test_processing_result_dataclass(self):
        """Test ProcessingResult dataclass."""
        result = ProcessingResult(
            request_id="test-123",
            processing_type="transcription",
            status=ProcessingStatus.COMPLETED,
            output_files=["result.txt"],
            metadata={"info": "test"}
        )
        
        assert result.request_id == "test-123"
        assert result.processing_type == "transcription"
        assert result.status == ProcessingStatus.COMPLETED
        assert result.output_files == ["result.txt"]
    
    def test_server_status_dataclass(self):
        """Test ServerStatus dataclass."""
        status = ServerStatus(
            server_type="diarization",
            status="running",
            port=9090
        )

        assert status.server_type == "diarization"
        assert status.status == "running"
        assert status.port == 9090
        assert status.pid is None  # Default value
        assert status.active_jobs == 0  # Default value

# Integration tests
class TestJsonProtocolIntegration:
    """Integration tests for JSON protocol components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.protocol = JsonProtocol()
        self.queue = MessageQueue()
    
    def test_full_message_lifecycle(self):
        """Test complete message creation, serialization, and processing."""
        # Create a processing request
        processing_request = ProcessingRequest(
            audio_file_path="/test/audio.wav",
            processing_type="diarization",
            parameters={"min_speakers": 1, "max_speakers": 5}
        )
        
        # Create message
        message = self.protocol.create_processing_request(processing_request)
        
        # Validate message
        validation = self.protocol.validate_message(message)
        assert validation['valid'] is True
        
        # Serialize message
        json_str = self.protocol.serialize_message(message)
        
        # Deserialize message
        deserialized = self.protocol.deserialize_message(json_str)
        
        # Verify round-trip preservation
        assert deserialized.message_type == message.message_type
        assert deserialized.payload == message.payload
        assert deserialized.message_id == message.message_id
        
        # Put in queue and retrieve
        self.queue.put_message(deserialized)
        retrieved = self.queue.get_message()
        
        assert retrieved is not None
        assert retrieved.message_id == message.message_id

if __name__ == "__main__":
    pytest.main([__file__, "-v"])