"""
Agent Communication Broker for multi-agent system
"""
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict
from threading import Lock
import asyncio
import json
from datetime import datetime
import logging

from src.agents.multi_agent_base import AgentMessage, MessageType, BaseAgent


class CommunicationBroker:
    """Central message broker for agent communication"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: List[AgentMessage] = []
        self.message_history: List[AgentMessage] = []
        self.subscriptions: Dict[str, List[str]] = defaultdict(list)
        self.lock = Lock()
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Message handlers by type
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.REQUEST: self._handle_request,
            MessageType.RESPONSE: self._handle_response,
            MessageType.BROADCAST: self._handle_broadcast,
            MessageType.DELEGATION: self._handle_delegation,
            MessageType.ESCALATION: self._handle_escalation,
            MessageType.STATUS_UPDATE: self._handle_status_update
        }
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the broker"""
        with self.lock:
            self.agents[agent.agent_id] = agent
            self.logger.info(f"Registered agent: {agent.agent_id}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        with self.lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                self.logger.info(f"Unregistered agent: {agent_id}")
    
    def subscribe_to_broadcasts(self, agent_id: str, topics: List[str]) -> None:
        """Subscribe agent to broadcast topics"""
        with self.lock:
            for topic in topics:
                self.subscriptions[topic].append(agent_id)
    
    def send_message(self, message: AgentMessage) -> None:
        """Queue a message for delivery"""
        if not isinstance(message, AgentMessage):
            raise TypeError("send_message expects an AgentMessage instance")

        with self.lock:
            self.message_queue.append(message)
            self.logger.debug(
                f"Queued message: {message.message_id} from {message.from_agent} to {message.to_agent}"
            )
    
    async def start(self) -> None:
        """Start the message broker"""
        self.running = True
        self.logger.info("Communication broker started")
        
        while self.running:
            await self._process_messages()
            await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
    
    def stop(self) -> None:
        """Stop the message broker"""
        self.running = False
        self.logger.info("Communication broker stopped")
    
    async def _process_messages(self) -> None:
        """Process queued messages"""
        messages_to_process = []
        
        with self.lock:
            messages_to_process = self.message_queue.copy()
            self.message_queue.clear()
        
        for message in messages_to_process:
            try:
                handler = self.message_handlers.get(message.message_type)
                if handler:
                    await handler(message)
                else:
                    self.logger.warning(f"No handler for message type: {message.message_type}")
                
                # Add to history
                self.message_history.append(message)
                
            except Exception as e:
                self.logger.error(f"Error processing message {message.message_id}: {str(e)}")
    
    async def _handle_request(self, message: AgentMessage) -> None:
        """Handle request messages"""
        target_agent = self.agents.get(message.to_agent)
        
        if not target_agent:
            self.logger.error(f"Target agent not found: {message.to_agent}")
            # Send error response back
            error_response = AgentMessage(
                from_agent="broker",
                to_agent=message.from_agent,
                message_type=MessageType.RESPONSE,
                task=f"error_{message.task}",
                payload={
                    "success": False,
                    "error": f"Agent {message.to_agent} not found"
                },
                context={},
                timestamp=datetime.now().isoformat(),
                parent_message_id=message.message_id
            )
            self.send_message(error_response)
            return
        
        # Deliver message to target agent
        response = target_agent.receive_message(message)

        if asyncio.iscoroutine(response) or isinstance(response, asyncio.Future):
            response = await response

        if isinstance(response, AgentMessage):
            self.send_message(response)
        elif response is not None:
            self.logger.warning(
                "Non-AgentMessage response returned from %s", target_agent.agent_id
            )
    
    async def _handle_response(self, message: AgentMessage) -> None:
        """Handle response messages"""
        target_agent = self.agents.get(message.to_agent)
        
        if target_agent:
            response = target_agent.receive_message(message)
            if asyncio.iscoroutine(response) or isinstance(response, asyncio.Future):
                response = await response

            if isinstance(response, AgentMessage):
                self.send_message(response)
            elif response is not None:
                self.logger.warning(
                    "Non-AgentMessage response returned from %s", target_agent.agent_id
                )
        else:
            self.logger.warning(f"Response target agent not found: {message.to_agent}")
    
    async def _handle_broadcast(self, message: AgentMessage) -> None:
        """Handle broadcast messages"""
        # Determine recipients based on task/topic
        recipients = []
        
        if message.to_agent == "*":
            # Broadcast to all agents
            recipients = list(self.agents.keys())
        else:
            # Topic-based broadcast
            topic = message.task
            recipients = self.subscriptions.get(topic, [])
        
        # Deliver to all recipients
        for agent_id in recipients:
            if agent_id != message.from_agent:  # Don't send back to sender
                agent = self.agents.get(agent_id)
                if agent:
                    agent.receive_message(message)
    
    async def _handle_delegation(self, message: AgentMessage) -> None:
        """Handle delegation messages"""
        # Similar to request but with special tracking
        await self._handle_request(message)
        
        # Could add delegation tracking here
        self.logger.info(f"Delegation from {message.from_agent} to {message.to_agent}: {message.task}")
    
    async def _handle_escalation(self, message: AgentMessage) -> None:
        """Handle escalation messages"""
        # Find appropriate escalation target
        escalation_target = message.to_agent
        
        if escalation_target == "orchestrator":
            # Special handling for orchestrator escalations
            self.logger.warning(f"Escalation to orchestrator: {message.payload.get('issue', 'Unknown issue')}")
        
        # Deliver escalation
        await self._handle_request(message)
    
    async def _handle_status_update(self, message: AgentMessage) -> None:
        """Handle status update messages"""
        # Log status update
        agent_id = message.payload.get("agent_id", message.from_agent)
        status = message.payload.get("status", "unknown")
        self.logger.info(f"Status update: {agent_id} is now {status}")
        
        # Broadcast to interested parties
        await self._handle_broadcast(message)
    
    def get_agent_status(self, agent_id: str) -> Optional[str]:
        """Get current status of an agent"""
        agent = self.agents.get(agent_id)
        return agent.status.value if agent else None
    
    def get_all_agent_statuses(self) -> Dict[str, str]:
        """Get status of all agents"""
        return {
            agent_id: agent.status.value 
            for agent_id, agent in self.agents.items()
        }
    
    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message history"""
        recent_messages = self.message_history[-limit:]
        return [msg.to_dict() for msg in recent_messages]
    
    def get_agent_conversation(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for specific agent"""
        agent_messages = [
            msg for msg in self.message_history
            if msg.from_agent == agent_id or msg.to_agent == agent_id
        ]
        return [msg.to_dict() for msg in agent_messages[-limit:]]


class AsyncCommunicationBroker(CommunicationBroker):
    """Async version of communication broker for better performance"""
    
    def __init__(self):
        super().__init__()
        self.message_tasks = []
    
    async def _process_messages(self) -> None:
        """Process messages concurrently"""
        messages_to_process = []
        
        with self.lock:
            messages_to_process = self.message_queue.copy()
            self.message_queue.clear()
        
        # Process messages concurrently
        tasks = []
        for message in messages_to_process:
            task = asyncio.create_task(self._process_single_message(message))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_message(self, message: AgentMessage) -> None:
        """Process a single message"""
        try:
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            
            # Add to history
            with self.lock:
                self.message_history.append(message)
                
        except Exception as e:
            self.logger.error(f"Error processing message {message.message_id}: {str(e)}")


def create_communication_broker(async_mode: bool = True) -> CommunicationBroker:
    """Factory function to create appropriate broker"""
    if async_mode:
        return AsyncCommunicationBroker()
    else:
        return CommunicationBroker()

