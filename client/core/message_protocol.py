"""Message protocol for WebRTC data channel communication with ACK/retry."""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Message types for the protocol."""
    CLIPBOARD_UPDATE = "CLIPBOARD_UPDATE"
    SNIPPET_SEND = "SNIPPET_SEND"
    ACK = "ACK"
    PING = "PING"
    PONG = "PONG"
    ERROR = "ERROR"


@dataclass
class Message:
    """Message envelope for WebRTC data channel."""
    id: str
    type: str
    timestamp: float
    from_device: str
    to_device: str
    payload: Dict[str, Any]
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(**data)
    
    @classmethod
    def create(cls, msg_type: str, from_device: str, to_device: str, payload: dict) -> 'Message':
        """Create a new message with auto-generated ID and timestamp."""
        return cls(
            id=str(uuid.uuid4()),
            type=msg_type,
            timestamp=time.time(),
            from_device=from_device,
            to_device=to_device,
            payload=payload
        )


@dataclass
class PendingMessage:
    """Tracks a message awaiting ACK."""
    message: Message
    send_time: float
    retry_count: int
    max_retries: int
    callback: Optional[Callable] = None


class MessageProtocol:
    """Handles message protocol with ACK and retry logic."""
    
    def __init__(self, device_id: str):
        """
        Initialize message protocol.
        
        Args:
            device_id: This device's ID
        """
        self.device_id = device_id
        self.pending_acks: Dict[str, PendingMessage] = {}
        self.retry_timeout = 2.0  # seconds
        self.max_retries = 5
        self.message_handlers: Dict[str, Callable] = {}
        self._retry_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Callbacks
        self.on_send: Optional[Callable] = None  # Called to actually send data
        self.on_message_failed: Optional[Callable] = None  # Called when message fails after retries
        
        logger.info(f"Message protocol initialized for device {device_id[:8]}...")
    
    def register_handler(self, msg_type: str, handler: Callable):
        """Register a handler for a message type."""
        self.message_handlers[msg_type] = handler
        logger.debug(f"Registered handler for {msg_type}")
    
    async def start(self):
        """Start the retry loop."""
        self._running = True
        self._retry_task = asyncio.create_task(self._retry_loop())
        logger.info("Message protocol retry loop started")
    
    async def stop(self):
        """Stop the retry loop."""
        self._running = False
        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass
        logger.info("Message protocol stopped")
    
    async def _retry_loop(self):
        """Background task to retry unacknowledged messages."""
        while self._running:
            try:
                await asyncio.sleep(0.5)
                await self._check_pending_messages()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retry loop: {e}", exc_info=True)
    
    async def _check_pending_messages(self):
        """Check and retry pending messages."""
        current_time = time.time()
        failed_messages = []
        
        for msg_id, pending in list(self.pending_acks.items()):
            elapsed = current_time - pending.send_time
            
            if elapsed >= self.retry_timeout:
                if pending.retry_count >= pending.max_retries:
                    # Max retries exceeded
                    logger.error(f"Message {msg_id[:8]} failed after {pending.max_retries} retries")
                    failed_messages.append(msg_id)
                else:
                    # Retry
                    pending.retry_count += 1
                    pending.send_time = current_time
                    logger.warning(f"Retrying message {msg_id[:8]} (attempt {pending.retry_count + 1})")
                    await self._send_raw(pending.message)
        
        # Handle failed messages
        for msg_id in failed_messages:
            pending = self.pending_acks.pop(msg_id, None)
            if pending and self.on_message_failed:
                await self.on_message_failed(pending.message)
    
    async def send_message(self, peer_id: str, msg_type: str, payload: dict, 
                          require_ack: bool = True, callback: Callable = None) -> str:
        """
        Send a message to a peer.
        
        Args:
            peer_id: Target device ID
            msg_type: Message type
            payload: Message payload
            require_ack: Whether to require ACK
            callback: Optional callback when ACK received
            
        Returns:
            Message ID
        """
        message = Message.create(msg_type, self.device_id, peer_id, payload)
        
        if require_ack and msg_type != MessageType.ACK:
            # Track for ACK
            self.pending_acks[message.id] = PendingMessage(
                message=message,
                send_time=time.time(),
                retry_count=0,
                max_retries=self.max_retries,
                callback=callback
            )
        
        await self._send_raw(message)
        logger.info(f"Sent {msg_type} to {peer_id[:8]} (id={message.id[:8]})")
        
        return message.id
    
    async def _send_raw(self, message: Message):
        """Send raw message via the send callback."""
        if self.on_send:
            try:
                await self.on_send(message.to_device, message.to_json())
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    async def handle_incoming(self, peer_id: str, data: str):
        """
        Handle incoming message.
        
        Args:
            peer_id: Source device ID
            data: Raw message JSON string
        """
        try:
            message = Message.from_json(data)
            logger.debug(f"Received {message.type} from {peer_id[:8]} (id={message.id[:8]})")
            
            # Handle ACK
            if message.type == MessageType.ACK:
                await self._handle_ack(message)
                return
            
            # Send ACK for non-ACK messages
            await self._send_ack(peer_id, message.id)
            
            # Dispatch to handler
            handler = self.message_handlers.get(message.type)
            if handler:
                await handler(peer_id, message)
            else:
                logger.warning(f"No handler for message type: {message.type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message from {peer_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling message from {peer_id}: {e}", exc_info=True)
    
    async def _handle_ack(self, message: Message):
        """Handle ACK message."""
        ack_id = message.payload.get('ack_id')
        if not ack_id:
            logger.warning("ACK message missing ack_id")
            return
        
        pending = self.pending_acks.pop(ack_id, None)
        if pending:
            logger.info(f"ACK received for {ack_id[:8]}")
            if pending.callback:
                await pending.callback(pending.message)
        else:
            logger.debug(f"ACK for unknown message: {ack_id[:8]}")
    
    async def _send_ack(self, peer_id: str, original_msg_id: str):
        """Send ACK for a message."""
        await self.send_message(
            peer_id,
            MessageType.ACK,
            {'ack_id': original_msg_id},
            require_ack=False
        )
    
    async def send_clipboard_update(self, peer_id: str, content: str, 
                                    device_name: str, callback: Callable = None) -> str:
        """
        Send clipboard update to a peer.
        
        Args:
            peer_id: Target device ID
            content: Clipboard content
            device_name: Sender device name
            callback: Optional callback when ACK received
            
        Returns:
            Message ID
        """
        return await self.send_message(
            peer_id,
            MessageType.CLIPBOARD_UPDATE,
            {
                'content': content,
                'device_name': device_name,
                'content_type': 'text'
            },
            require_ack=True,
            callback=callback
        )
    
    async def send_snippet(self, peer_id: str, text: str, 
                          device_name: str, callback: Callable = None) -> str:
        """
        Send text snippet to a peer.
        
        Args:
            peer_id: Target device ID
            text: Snippet text
            device_name: Sender device name
            callback: Optional callback when ACK received
            
        Returns:
            Message ID
        """
        return await self.send_message(
            peer_id,
            MessageType.SNIPPET_SEND,
            {
                'text': text,
                'device_name': device_name
            },
            require_ack=True,
            callback=callback
        )
    
    async def send_ping(self, peer_id: str) -> str:
        """Send ping to a peer."""
        return await self.send_message(
            peer_id,
            MessageType.PING,
            {},
            require_ack=True
        )
    
    def get_pending_count(self) -> int:
        """Get number of pending messages."""
        return len(self.pending_acks)
    
    def get_pending_for_peer(self, peer_id: str) -> int:
        """Get number of pending messages for a peer."""
        return sum(1 for p in self.pending_acks.values() 
                   if p.message.to_device == peer_id)
