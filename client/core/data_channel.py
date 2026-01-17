"""RTC Data Channel handler for clipboard data transmission."""
import json
import logging
import asyncio
from typing import Callable, Optional, Dict
from aiortc import RTCDataChannel

logger = logging.getLogger(__name__)

class DataChannelHandler:
    """Manages RTC Data Channels for clipboard synchronization."""

    def __init__(self):
        """Initialize the data channel handler."""
        self.channels: Dict[str, RTCDataChannel] = {}  # peer_id -> channel
        self.message_callback: Optional[Callable] = None
        self.open_callback: Optional[Callable] = None
        self.close_callback: Optional[Callable] = None
        logger.info("Data channel handler initialized")

    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages."""
        self.message_callback = callback
        logger.debug("Message callback registered")

    def set_open_callback(self, callback: Callable):
        """Set callback for channel open events."""
        self.open_callback = callback
        logger.debug("Open callback registered")

    def set_close_callback(self, callback: Callable):
        """Set callback for channel close events."""
        self.close_callback = callback
        logger.debug("Close callback registered")

    def create_data_channel(self, peer_connection, peer_id: str, channel_name: str = 'clipboard'):
        """
        Create a data channel for a peer.

        Args:
            peer_connection: RTCPeerConnection instance
            peer_id: ID of the peer device
            channel_name: Name of the data channel

        Returns:
            RTCDataChannel: Created data channel
        """
        try:
            channel = peer_connection.createDataChannel(channel_name)
            self.channels[peer_id] = channel

            # Set up event handlers
            @channel.on('open')
            def on_open():
                logger.info(f"Data channel opened with peer: {peer_id}")
                if self.open_callback:
                    asyncio.create_task(self.open_callback(peer_id))

            @channel.on('message')
            def on_message(message):
                logger.debug(f"Received message from {peer_id}: {len(message)} bytes")
                if self.message_callback:
                    asyncio.create_task(self._handle_message(peer_id, message))

            @channel.on('close')
            def on_close():
                logger.info(f"Data channel closed with peer: {peer_id}")
                if peer_id in self.channels:
                    del self.channels[peer_id]
                if self.close_callback:
                    asyncio.create_task(self.close_callback(peer_id))

            logger.info(f"Data channel created for peer: {peer_id}")
            return channel

        except Exception as e:
            logger.error(f"Error creating data channel for {peer_id}: {e}", exc_info=True)
            raise

    def handle_data_channel(self, peer_id: str, channel: RTCDataChannel):
        """
        Handle an incoming data channel from a peer.

        Args:
            peer_id: ID of the peer device
            channel: RTCDataChannel instance
        """
        try:
            self.channels[peer_id] = channel
            logger.info(f"Received data channel from peer: {peer_id}")

            @channel.on('open')
            def on_open():
                logger.info(f"Incoming data channel opened with peer: {peer_id}")
                if self.open_callback:
                    asyncio.create_task(self.open_callback(peer_id))

            @channel.on('message')
            def on_message(message):
                logger.debug(f"Received message from {peer_id}: {len(message)} bytes")
                if self.message_callback:
                    asyncio.create_task(self._handle_message(peer_id, message))

            @channel.on('close')
            def on_close():
                logger.info(f"Incoming data channel closed with peer: {peer_id}")
                if peer_id in self.channels:
                    del self.channels[peer_id]
                if self.close_callback:
                    asyncio.create_task(self.close_callback(peer_id))

        except Exception as e:
            logger.error(f"Error handling data channel from {peer_id}: {e}", exc_info=True)

    async def _handle_message(self, peer_id: str, message: str):
        """
        Internal method to handle incoming messages.

        Args:
            peer_id: ID of the peer device
            message: Message string
        """
        try:
            data = json.loads(message)
            logger.debug(f"Parsed message from {peer_id}: type={data.get('type')}")

            if self.message_callback:
                await self.message_callback(peer_id, data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message from {peer_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling message from {peer_id}: {e}", exc_info=True)

    async def send_clipboard_data(self, peer_id: str, content: str, metadata: dict):
        """
        Send clipboard data to a peer.

        Args:
            peer_id: ID of the peer device
            content: Clipboard content
            metadata: Additional metadata (timestamp, device info, etc.)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            channel = self.channels.get(peer_id)
            if not channel:
                logger.warning(f"No data channel available for peer: {peer_id}")
                return False

            if channel.readyState != 'open':
                logger.warning(f"Data channel not open for peer: {peer_id} (state: {channel.readyState})")
                return False

            message = {
                'type': 'clipboard_update',
                'content': content,
                'metadata': metadata
            }

            message_str = json.dumps(message)
            channel.send(message_str)

            logger.info(f"Sent clipboard data to {peer_id}: {len(content)} chars")
            return True

        except Exception as e:
            logger.error(f"Error sending clipboard data to {peer_id}: {e}", exc_info=True)
            return False

    def is_channel_open(self, peer_id: str) -> bool:
        """
        Check if a data channel is open.

        Args:
            peer_id: ID of the peer device

        Returns:
            bool: True if channel is open, False otherwise
        """
        channel = self.channels.get(peer_id)
        if channel:
            is_open = channel.readyState == 'open'
            logger.debug(f"Channel state for {peer_id}: {channel.readyState}")
            return is_open
        return False

    def close_channel(self, peer_id: str):
        """
        Close a data channel.

        Args:
            peer_id: ID of the peer device
        """
        try:
            channel = self.channels.get(peer_id)
            if channel:
                channel.close()
                logger.info(f"Closed data channel for peer: {peer_id}")

            if peer_id in self.channels:
                del self.channels[peer_id]

        except Exception as e:
            logger.error(f"Error closing data channel for {peer_id}: {e}", exc_info=True)

    def close_all_channels(self):
        """Close all data channels."""
        logger.info("Closing all data channels")
        peer_ids = list(self.channels.keys())
        for peer_id in peer_ids:
            self.close_channel(peer_id)
