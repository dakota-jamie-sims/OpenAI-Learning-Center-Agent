"""
Agent communication system for message passing and coordination
"""
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
from queue import Queue, PriorityQueue
import threading
import json
import uuid
from enum import Enum

from src.agents.multi_agent_base import AgentMessage, MessageType, BaseAgent, AgentStatus


class MessagePriority(Enum):
    """Message priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class PrioritizedMessage(BaseModel):
    """Message with priority for queue processing"""
    priority: int
    message: AgentMessage
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    
    class Config:
        # Enable comparison based on priority
        allow_mutation = True
    
    def __lt__(self, other):
        """Compare messages by priority for queue ordering"""
        if isinstance(other, PrioritizedMessage):
            return self.priority < other.priority
        return NotImplemented
    
    def __eq__(self, other):
        """Check equality based on priority"""
        if isinstance(other, PrioritizedMessage):
            return self.priority == other.priority
        return NotImplemented


class MessageBroker:
    """Central message broker for agent communication"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue = PriorityQueue()
        self.message_history: List[AgentMessage] = []
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> agent_ids
        self.routing_table: Dict[str, str] = {}  # agent_id -> team
        self.running = False
        self.processing_thread = None
        
        # Message tracking
        self.message_stats = {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "retried": 0
        }
        
        # Callbacks
        self.message_callbacks: Dict[str, List[Callable]] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the broker"""
        self.agents[agent.agent_id] = agent
        
        # Update routing table
        if agent.team:
            self.routing_table[agent.agent_id] = agent.team
        
        print(f"📡 Registered agent: {agent.agent_id} (team: {agent.team})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            
            # Clean up subscriptions
            for topic, subscribers in self.subscriptions.items():
                if agent_id in subscribers:
                    subscribers.remove(agent_id)
            
            print(f"👋 Unregistered agent: {agent_id}")
    
    def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        
        if agent_id not in self.subscriptions[topic]:
            self.subscriptions[topic].append(agent_id)
            print(f"📬 {agent_id} subscribed to topic: {topic}")
    
    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a topic"""
        if topic in self.subscriptions and agent_id in self.subscriptions[topic]:
            self.subscriptions[topic].remove(agent_id)
            print(f"📭 {agent_id} unsubscribed from topic: {topic}")
    
    def send_message(self, message: AgentMessage, priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send a message through the broker"""
        # Add message ID if not present
        if not message.message_id:
            message.message_id = str(uuid.uuid4())
        
        # Create prioritized message
        prioritized_msg = PrioritizedMessage(
            priority=priority.value,
            message=message
        )
        
        # Add to queue
        self.message_queue.put(prioritized_msg)
        self.message_stats["sent"] += 1
        
        # Trigger callbacks
        self._trigger_callbacks("message_sent", message)
        
        return message.message_id
    
    def broadcast(self, message: AgentMessage, topic: str = None) -> List[str]:
        """Broadcast a message to multiple agents"""
        message.message_type = MessageType.BROADCAST
        
        if topic and topic in self.subscriptions:
            # Send to topic subscribers
            recipients = self.subscriptions[topic]
        else:
            # Send to all agents except sender
            recipients = [aid for aid in self.agents.keys() if aid != message.from_agent]
        
        message_ids = []
        for recipient in recipients:
            broadcast_msg = AgentMessage(
                from_agent=message.from_agent,
                to_agent=recipient,
                message_type=MessageType.BROADCAST,
                task=message.task,
                payload=message.payload,
                context=message.context,
                timestamp=message.timestamp,
                parent_message_id=message.message_id
            )
            msg_id = self.send_message(broadcast_msg)
            message_ids.append(msg_id)
        
        return message_ids
    
    def start(self) -> None:
        """Start the message broker"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_messages)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            print("🚀 Message broker started")
    
    def stop(self) -> None:
        """Stop the message broker"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        print("🛑 Message broker stopped")
    
    def _process_messages(self) -> None:
        """Process messages from the queue"""
        while self.running:
            try:
                # Get message with timeout
                prioritized_msg = self.message_queue.get(timeout=1)
                message = prioritized_msg.message
                
                # Process message
                success = self._deliver_message(message)
                
                if success:
                    self.message_stats["delivered"] += 1
                    self.message_history.append(message)
                else:
                    self.message_stats["failed"] += 1
                    
                    # Retry if within limits
                    if prioritized_msg.retry_count < prioritized_msg.max_retries:
                        prioritized_msg.retry_count += 1
                        self.message_stats["retried"] += 1
                        
                        # Re-queue with lower priority
                        prioritized_msg.priority = min(
                            MessagePriority.LOW.value,
                            prioritized_msg.priority + 1
                        )
                        self.message_queue.put(prioritized_msg)
                    else:
                        # Max retries exceeded
                        self._handle_failed_message(message)
                
                self.message_queue.task_done()
                
            except:
                # Timeout - continue loop
                continue
    
    def _deliver_message(self, message: AgentMessage) -> bool:
        """Deliver a message to the target agent"""
        # Check if target agent exists
        if message.to_agent not in self.agents:
            if message.to_agent == "*":
                # Broadcast message handled separately
                return True
            
            print(f"❌ Agent not found: {message.to_agent}")
            return False
        
        target_agent = self.agents[message.to_agent]
        
        try:
            # Check if agent is available
            if target_agent.status == AgentStatus.ERROR:
                print(f"⚠️ Target agent in error state: {message.to_agent}")
                return False
            
            # Deliver message
            response = target_agent.receive_message(message)
            
            # If response generated, queue it
            if response and response.to_agent != message.from_agent:
                self.send_message(response)
            
            # Trigger delivery callback
            self._trigger_callbacks("message_delivered", message)
            
            return True
            
        except Exception as e:
            print(f"❌ Error delivering message: {str(e)}")
            return False
    
    def _handle_failed_message(self, message: AgentMessage) -> None:
        """Handle a message that failed to deliver"""
        print(f"💀 Message delivery failed: {message.message_id}")
        
        # Send failure notification to sender
        if message.from_agent in self.agents:
            failure_msg = AgentMessage(
                from_agent="message_broker",
                to_agent=message.from_agent,
                message_type=MessageType.RESPONSE,
                task="delivery_failure",
                payload={
                    "failed_message_id": message.message_id,
                    "original_task": message.task,
                    "target_agent": message.to_agent,
                    "reason": "Max retries exceeded"
                },
                context={},
                timestamp=datetime.now().isoformat()
            )
            self.send_message(failure_msg, MessagePriority.HIGH)
        
        # Trigger failure callback
        self._trigger_callbacks("message_failed", message)
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for message events"""
        if event not in self.message_callbacks:
            self.message_callbacks[event] = []
        
        self.message_callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, message: AgentMessage) -> None:
        """Trigger callbacks for an event"""
        if event in self.message_callbacks:
            for callback in self.message_callbacks[event]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"❌ Callback error: {str(e)}")
    
    def get_message_history(self, agent_id: str = None, limit: int = 100) -> List[AgentMessage]:
        """Get message history"""
        if agent_id:
            # Filter by agent
            history = [
                msg for msg in self.message_history
                if msg.from_agent == agent_id or msg.to_agent == agent_id
            ]
        else:
            history = self.message_history
        
        return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message broker statistics"""
        return {
            "agents_registered": len(self.agents),
            "messages_sent": self.message_stats["sent"],
            "messages_delivered": self.message_stats["delivered"],
            "messages_failed": self.message_stats["failed"],
            "messages_retried": self.message_stats["retried"],
            "queue_size": self.message_queue.qsize(),
            "delivery_rate": (
                self.message_stats["delivered"] / self.message_stats["sent"] * 100
                if self.message_stats["sent"] > 0 else 0
            )
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        return {
            "agent_id": agent_id,
            "status": agent.status.value,
            "team": agent.team,
            "capabilities": agent.capabilities,
            "message_queue_size": len(agent.message_queue)
        }


class CommunicationProtocol:
    """Protocol for structured agent communication"""
    
    @staticmethod
    def create_request(from_agent: str, to_agent: str, task: str, 
                      payload: Dict[str, Any], context: Dict[str, Any] = None) -> AgentMessage:
        """Create a request message"""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.REQUEST,
            task=task,
            payload=payload,
            context=context or {},
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def create_response(original_message: AgentMessage, payload: Dict[str, Any], 
                       success: bool = True) -> AgentMessage:
        """Create a response message"""
        return AgentMessage(
            from_agent=original_message.to_agent,
            to_agent=original_message.from_agent,
            message_type=MessageType.RESPONSE,
            task=f"response_{original_message.task}",
            payload={
                "success": success,
                **payload
            },
            context=original_message.context,
            timestamp=datetime.now().isoformat(),
            parent_message_id=original_message.message_id
        )
    
    @staticmethod
    def create_delegation(from_agent: str, to_agent: str, task: str,
                         payload: Dict[str, Any], parent_task: str = None) -> AgentMessage:
        """Create a delegation message"""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.DELEGATION,
            task=task,
            payload=payload,
            context={
                "parent_task": parent_task,
                "delegated_at": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def create_escalation(from_agent: str, issue: str, details: Dict[str, Any],
                         team_lead: str = None) -> AgentMessage:
        """Create an escalation message"""
        to_agent = team_lead or "orchestrator"
        
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.ESCALATION,
            task="handle_escalation",
            payload={
                "issue": issue,
                "details": details,
                "escalated_at": datetime.now().isoformat()
            },
            context={
                "escalation_reason": issue
            },
            timestamp=datetime.now().isoformat()
        )
    
    @staticmethod
    def parse_message(message_json: str) -> AgentMessage:
        """Parse a message from JSON"""
        data = json.loads(message_json)
        return AgentMessage.from_dict(data)
    
    @staticmethod
    def serialize_message(message: AgentMessage) -> str:
        """Serialize a message to JSON"""
        return json.dumps(message.to_dict())


class AgentCommunicationInterface:
    """Interface for agents to communicate through the broker"""
    
    def __init__(self, agent: BaseAgent, broker: MessageBroker):
        self.agent = agent
        self.broker = broker
        
        # Register agent with broker
        self.broker.register_agent(agent)
        
        # Subscribe to team topics
        if agent.team:
            self.broker.subscribe(agent.agent_id, f"team_{agent.team}")
        
        # Subscribe to broadcast topic
        self.broker.subscribe(agent.agent_id, "all_agents")
    
    def send_message(self, to_agent: str, task: str, payload: Dict[str, Any],
                    priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send a message to another agent"""
        message = CommunicationProtocol.create_request(
            self.agent.agent_id,
            to_agent,
            task,
            payload
        )
        return self.broker.send_message(message, priority)
    
    def broadcast_to_team(self, task: str, payload: Dict[str, Any]) -> List[str]:
        """Broadcast message to team members"""
        if not self.agent.team:
            return []
        
        message = AgentMessage(
            from_agent=self.agent.agent_id,
            to_agent="*",
            message_type=MessageType.BROADCAST,
            task=task,
            payload=payload,
            context={"team": self.agent.team},
            timestamp=datetime.now().isoformat()
        )
        
        return self.broker.broadcast(message, f"team_{self.agent.team}")
    
    def delegate_task(self, to_agent: str, task: str, payload: Dict[str, Any]) -> str:
        """Delegate a task to another agent"""
        message = CommunicationProtocol.create_delegation(
            self.agent.agent_id,
            to_agent,
            task,
            payload
        )
        return self.broker.send_message(message, MessagePriority.HIGH)
    
    def escalate_issue(self, issue: str, details: Dict[str, Any]) -> str:
        """Escalate an issue to team lead or orchestrator"""
        team_lead = f"{self.agent.team}_lead" if self.agent.team else None
        message = CommunicationProtocol.create_escalation(
            self.agent.agent_id,
            issue,
            details,
            team_lead
        )
        return self.broker.send_message(message, MessagePriority.CRITICAL)
    
    def get_message_history(self, limit: int = 50) -> List[AgentMessage]:
        """Get agent's message history"""
        return self.broker.get_message_history(self.agent.agent_id, limit)
    
    def get_pending_messages(self) -> List[AgentMessage]:
        """Get pending messages for the agent"""
        return list(self.agent.message_queue)


# Global message broker instance
global_message_broker = MessageBroker()


def initialize_communication_system() -> MessageBroker:
    """Initialize the global communication system"""
    global_message_broker.start()
    
    # Register event callbacks
    global_message_broker.register_callback(
        "message_delivered",
        lambda msg: print(f"✅ Delivered: {msg.from_agent} → {msg.to_agent} ({msg.task})")
    )
    
    global_message_broker.register_callback(
        "message_failed",
        lambda msg: print(f"❌ Failed: {msg.from_agent} → {msg.to_agent} ({msg.task})")
    )
    
    return global_message_broker


def shutdown_communication_system() -> None:
    """Shutdown the communication system"""
    global_message_broker.stop()
    print("📡 Communication system shutdown complete")