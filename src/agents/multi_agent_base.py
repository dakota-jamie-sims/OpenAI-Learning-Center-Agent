"""
Base agent class for multi-agent system
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import json
import uuid
from dataclasses import dataclass, asdict

from src.services.openai_responses_client import ResponsesClient
from src.config import DEFAULT_MODELS


class MessageType(Enum):
    """Types of messages between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    DELEGATION = "delegation"
    ESCALATION = "escalation"
    STATUS_UPDATE = "status_update"


class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentMessage:
    """Standardized message format for agent communication"""
    from_agent: str
    to_agent: str
    message_type: MessageType
    task: str
    payload: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: str
    message_id: str = None
    parent_message_id: str = None
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, agent_id: str, agent_type: str, team: str = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.team = team
        self.status = AgentStatus.IDLE
        self.memory: List[AgentMessage] = []
        self.context: Dict[str, Any] = {}
        self.responses_client = ResponsesClient()
        self.model = DEFAULT_MODELS.get(agent_type.lower(), "gpt-5")
        self.message_queue: List[AgentMessage] = []
        self.capabilities: List[str] = []
        self.dependencies: List[str] = []
        
    @abstractmethod
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process incoming message and return response"""
        pass
    
    @abstractmethod
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if agent can handle the task"""
        pass
    
    def receive_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Receive and process a message"""
        # Add to memory
        self.memory.append(message)
        
        # Validate task
        is_valid, reason = self.validate_task(message.task, message.payload)
        
        if not is_valid:
            return self._create_error_response(message, reason)
        
        # Update status
        self.status = AgentStatus.WORKING
        
        try:
            # Process the message
            response = self.process_message(message)
            self.status = AgentStatus.IDLE
            return response
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            return self._create_error_response(message, str(e))
    
    def send_message(self, to_agent: str, task: str, payload: Dict[str, Any], 
                    message_type: MessageType = MessageType.REQUEST) -> AgentMessage:
        """Create and send a message to another agent"""
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            task=task,
            payload=payload,
            context=self.context,
            timestamp=datetime.now().isoformat()
        )
        
        # In a real implementation, this would send to a message broker
        # For now, we'll add to queue
        self.message_queue.append(message)
        return message
    
    def broadcast_message(self, task: str, payload: Dict[str, Any]) -> AgentMessage:
        """Broadcast a message to all agents"""
        return self.send_message(
            to_agent="*",  # Broadcast to all
            task=task,
            payload=payload,
            message_type=MessageType.BROADCAST
        )
    
    def delegate_task(self, to_agent: str, task: str, payload: Dict[str, Any]) -> AgentMessage:
        """Delegate a task to a sub-agent"""
        return self.send_message(
            to_agent=to_agent,
            task=task,
            payload=payload,
            message_type=MessageType.DELEGATION
        )
    
    def escalate_issue(self, issue: str, details: Dict[str, Any]) -> AgentMessage:
        """Escalate an issue to team lead or orchestrator"""
        escalation_target = f"{self.team}_lead" if self.team else "orchestrator"
        
        return self.send_message(
            to_agent=escalation_target,
            task="handle_escalation",
            payload={
                "issue": issue,
                "details": details,
                "agent_status": self.status.value
            },
            message_type=MessageType.ESCALATION
        )
    
    def update_status(self, status: AgentStatus, details: str = "") -> None:
        """Update agent status and notify interested parties"""
        self.status = status
        
        # Send status update
        self.broadcast_message(
            task="status_update",
            payload={
                "agent_id": self.agent_id,
                "status": status.value,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _create_error_response(self, original_message: AgentMessage, error: str) -> AgentMessage:
        """Create an error response message"""
        return AgentMessage(
            from_agent=self.agent_id,
            to_agent=original_message.from_agent,
            message_type=MessageType.RESPONSE,
            task=f"error_{original_message.task}",
            payload={
                "success": False,
                "error": error,
                "original_task": original_message.task
            },
            context=self.context,
            timestamp=datetime.now().isoformat(),
            parent_message_id=original_message.message_id
        )
    
    def _create_response(self, original_message: AgentMessage, 
                        payload: Dict[str, Any]) -> AgentMessage:
        """Create a response message"""
        return AgentMessage(
            from_agent=self.agent_id,
            to_agent=original_message.from_agent,
            message_type=MessageType.RESPONSE,
            task=f"response_{original_message.task}",
            payload=payload,
            context=self.context,
            timestamp=datetime.now().isoformat(),
            parent_message_id=original_message.message_id
        )
    
    def query_llm(self, prompt: str, reasoning_effort: str = "medium", 
                  verbosity: str = "medium", **kwargs) -> str:
        """Query the LLM with the agent's specialized model"""
        return self.responses_client.create_response(
            model=self.model,
            input_text=prompt,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            **kwargs
        )
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        recent_messages = self.memory[-limit:]
        return [msg.to_dict() for msg in recent_messages]
    
    def clear_memory(self) -> None:
        """Clear agent memory"""
        self.memory.clear()
    
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return self.capabilities
    
    def add_capability(self, capability: str) -> None:
        """Add a new capability"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, type={self.agent_type}, status={self.status.value})"