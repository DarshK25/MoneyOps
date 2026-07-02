from typing import Dict, Any, List, Optional, Callable, Awaitable, Set
from datetime import datetime
import asyncio
import time
import uuid

from app.agentos.types import AgentMessage, MessageType, MessageStatus
from app.agentos.memory import agent_memory
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MessageBus:
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._message_history: List[AgentMessage] = []
        self._max_history = 500
        self._lock = asyncio.Lock()
        self._latency: Dict[str, List[float]] = {}

    async def register_agent(self, agent_name: str):
        async with self._lock:
            if agent_name not in self._queues:
                self._queues[agent_name] = asyncio.Queue(maxsize=500)
                self._handlers[agent_name] = []
                logger.info("message_bus_agent_registered", agent=agent_name)

    async def register_handler(self, agent_name: str, handler: Callable):
        async with self._lock:
            if agent_name not in self._handlers:
                self._handlers[agent_name] = []
            self._handlers[agent_name].append(handler)

    async def send(self, message: AgentMessage) -> bool:
        try:
            message.timestamp = time.time()
            message.status = MessageStatus.PENDING

            target_queue = self._queues.get(message.receiver)
            if target_queue is None:
                logger.warning("message_bus_no_receiver", receiver=message.receiver, sender=message.sender)
                message.status = MessageStatus.FAILED
                await self._archive(message)
                return False

            await target_queue.put(message)
            message.status = MessageStatus.DELIVERED
            await self._archive(message)

            agent_memory.store_communication(message.message_id, message.to_dict())

            ns = f"latency:{message.message_type.value}"
            if ns not in self._latency:
                self._latency[ns] = []
            self._latency[ns].append(time.time())

            return True
        except Exception as e:
            logger.error("message_bus_send_failed", error=str(e), sender=message.sender, receiver=message.receiver)
            message.status = MessageStatus.FAILED
            message.error = str(e)
            await self._archive(message)
            return False

    async def receive(self, agent_name: str, timeout: float = 30.0) -> Optional[AgentMessage]:
        queue = self._queues.get(agent_name)
        if queue is None:
            return None
        try:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            message.status = MessageStatus.READ
            return message
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error("message_bus_receive_error", agent=agent_name, error=str(e))
            return None

    async def request(self, sender: str, receiver: str, payload: Dict[str, Any],
                      message_type: MessageType = MessageType.REQUEST,
                      context: Optional[Dict[str, Any]] = None,
                      reasoning: str = "", priority: int = 3,
                      org_id: str = "", session_id: str = "") -> Optional[AgentMessage]:
        correlation_id = str(uuid.uuid4())
        msg = AgentMessage(
            message_type=message_type,
            sender=sender,
            receiver=receiver,
            payload=payload,
            context=context or {},
            reasoning=reasoning,
            requested_action=payload.get("action", ""),
            priority=priority,
            correlation_id=correlation_id,
            org_id=org_id,
            session_id=session_id,
        )
        sent = await self.send(msg)
        if not sent:
            return None
        response = await self.receive(sender, timeout=30.0)
        if response and response.correlation_id == correlation_id:
            return response
        return None

    async def respond(self, original: AgentMessage, payload: Dict[str, Any],
                      message_type: MessageType = MessageType.RESPONSE,
                      reasoning: str = "") -> bool:
        response = AgentMessage(
            message_type=message_type,
            sender=original.receiver,
            receiver=original.sender,
            payload=payload,
            context=original.context,
            reasoning=reasoning,
            correlation_id=original.correlation_id,
            org_id=original.org_id,
            session_id=original.session_id,
        )
        return await self.send(response)

    async def broadcast(self, sender: str, message_type: MessageType,
                        payload: Dict[str, Any], org_id: str = "",
                        priority: int = 3):
        async with self._lock:
            agents = list(self._queues.keys())
        tasks = []
        for receiver in agents:
            if receiver == sender:
                continue
            msg = AgentMessage(
                message_type=message_type,
                sender=sender,
                receiver=receiver,
                payload=payload,
                org_id=org_id,
                priority=priority,
            )
            tasks.append(self.send(msg))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def process_agent_queue(self, agent_name: str):
        queue = self._queues.get(agent_name)
        handlers = self._handlers.get(agent_name, [])
        if queue is None or not handlers:
            return
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                message.status = MessageStatus.PROCESSED
                for handler in handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    except Exception as e:
                        logger.error("message_bus_handler_error", agent=agent_name, error=str(e))
            except asyncio.TimeoutError:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error("message_bus_process_error", agent=agent_name, error=str(e))

    async def get_message_history(self, limit: int = 50,
                                  sender: Optional[str] = None,
                                  receiver: Optional[str] = None,
                                  message_type: Optional[MessageType] = None) -> List[Dict[str, Any]]:
        messages = list(self._message_history)
        if sender:
            messages = [m for m in messages if m.sender == sender]
        if receiver:
            messages = [m for m in messages if m.receiver == receiver]
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        return [m.to_dict() for m in messages[-limit:]]

    async def get_agent_conversation(self, agent_a: str, agent_b: str,
                                     limit: int = 50) -> List[Dict[str, Any]]:
        messages = list(self._message_history)
        filtered = [m for m in messages
                    if (m.sender == agent_a and m.receiver == agent_b) or
                       (m.sender == agent_b and m.receiver == agent_a)]
        return [m.to_dict() for m in filtered[-limit:]]

    async def get_stats(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "registered_agents": list(self._queues.keys()),
                "total_messages": len(self._message_history),
                "queue_sizes": {name: q.qsize() for name, q in self._queues.items()},
            }

    async def _archive(self, message: AgentMessage):
        async with self._lock:
            self._message_history.append(message)
            if len(self._message_history) > self._max_history:
                self._message_history = self._message_history[-self._max_history:]


message_bus = MessageBus()
