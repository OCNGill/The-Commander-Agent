"""
Test Suite: Protocol Layer
Tests for commander_os.core.protocol

Run with: pytest tests/core/test_protocol.py -v
"""

import pytest
from commander_os.core.protocol import (
    CommanderProtocol, 
    MessageEnvelope, 
    MessageType, 
    TaskDefinition, 
    TaskStatus
)

class TestProtocol:
    """Tests for the Protocol Layer."""

    def test_message_envelope_defaults(self):
        """Test default values for MessageEnvelope."""
        msg = MessageEnvelope(
            msg_type=MessageType.COMMAND,
            sender_id="commander",
            recipient_id="agent-1"
        )
        
        assert msg.id is not None
        assert msg.timestamp > 0
        assert msg.payload == {}

    def test_task_definition_defaults(self):
        """Test default values for TaskDefinition."""
        task = TaskDefinition(
            title="Fix bug",
            description="Fix the critical bug",
            assigned_to_role="coder"
        )
        
        assert task.id is not None
        assert task.status == TaskStatus.PENDING

    def test_create_command_factory(self):
        """Test the create_command factory method."""
        msg = CommanderProtocol.create_command(
            sender_id="commander",
            recipient_id="agent-coder",
            command="write_file",
            params={"file": "test.py"},
            task_id="task-123"
        )
        
        assert msg.msg_type == MessageType.COMMAND
        assert msg.task_id == "task-123"
        assert msg.payload["command"] == "write_file"

    def test_create_response_factory(self):
        """Test the create_response factory method."""
        original = MessageEnvelope(
            id="msg-1",
            msg_type=MessageType.COMMAND,
            sender_id="commander",
            recipient_id="agent-1"
        )
        
        response = CommanderProtocol.create_response(
            original_msg=original,
            response_data={"result": "done"},
            status="success"
        )
        
        assert response.msg_type == MessageType.RESPONSE
        assert response.correlation_id == "msg-1"
        assert response.recipient_id == "commander"
        assert response.sender_id == "agent-1"
