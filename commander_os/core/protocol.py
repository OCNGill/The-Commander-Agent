"""
The-Commander: Protocol Layer
Defines the authoritative communication standards, task lifecycles, and message schemas.

This layer enforces the Commander's orchestration rules across the cluster.

Version: 1.0.0
"""

import uuid
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

# -------------------------------------------------------------------------
# Enums
# -------------------------------------------------------------------------

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MessageType(str, Enum):
    COMMAND = "command"        # Direct instruction from Commander
    RESPONSE = "response"      # Implementation or answer from Agent
    QUERY = "query"            # Info request (memory/status)
    EVENT = "event"            # Asynchronous notification
    ERROR = "error"            # Protocol violation or failure
    HEARTBEAT = "heartbeat"    # Lifeliness check

class PriorityLevel(int, Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4

# -------------------------------------------------------------------------
# Message Schema
# -------------------------------------------------------------------------

class MessageEnvelope(BaseModel):
    """
    Standard communication envelope for all protocol traffic.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    msg_type: MessageType
    
    sender_id: str
    recipient_id: Union[str, List[str]]
    
    task_id: Optional[str] = None
    priority: PriorityLevel = PriorityLevel.NORMAL
    
    # Payload is generic, but should adhere to specific schemas based on type
    payload: Dict[str, Any] = {}
    
    # Traceability
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

# -------------------------------------------------------------------------
# Task Definition
# -------------------------------------------------------------------------

class TaskDefinition(BaseModel):
    """
    Authoritative definition of a unit of work.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    title: str
    description: str
    
    # Architecture alignment
    assigned_to_role: str  # Desired role (e.g., 'coder')
    assigned_agent_id: Optional[str] = None
    
    status: TaskStatus = TaskStatus.PENDING
    
    # Constraints & Context
    context_files: List[str] = []
    dependencies: List[str] = []
    
    output_requirements: str = "Return a valid response."

# -------------------------------------------------------------------------
# Protocol Logic
# -------------------------------------------------------------------------

class CommanderProtocol:
    """
    Enforces the rules of engagement for the cluster.
    """
    
    @staticmethod
    def validate_envelope(envelope: MessageEnvelope) -> bool:
        """
        Validate that a message adheres to protocol standards.
        """
        if not envelope.sender_id or not envelope.recipient_id:
            return False
        return True
        
    @staticmethod
    def create_command(
        sender_id: str,
        recipient_id: str,
        command: str,
        params: Dict[str, Any] = {},
        task_id: Optional[str] = None
    ) -> MessageEnvelope:
        """
        Factory for creating standard Command messages.
        """
        return MessageEnvelope(
            msg_type=MessageType.COMMAND,
            sender_id=sender_id,
            recipient_id=recipient_id,
            task_id=task_id,
            priority=PriorityLevel.HIGH, # Commands are usually high priority
            payload={
                "command": command,
                "params": params
            }
        )
        
    @staticmethod
    def create_response(
        original_msg: MessageEnvelope,
        response_data: Any,
        status: str = "success"
    ) -> MessageEnvelope:
        """
        Factory for replying to a message.
        """
        return MessageEnvelope(
            correlation_id=original_msg.id,
            task_id=original_msg.task_id,
            sender_id=original_msg.recipient_id if isinstance(original_msg.recipient_id, str) else "unknown",
            recipient_id=original_msg.sender_id,
            msg_type=MessageType.RESPONSE,
            payload={
                "status": status,
                "data": response_data
            }
        )
