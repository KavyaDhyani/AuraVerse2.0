"""WebSocket client for signaling server communication."""
import socketio
import logging
import asyncio
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

class SignalingClient:
    """WebSocket client for signaling server."""

    def __init__(self, server_url: str):
        """
        Initialize signaling client.

        Args:
            server_url: URL of the signaling server
        """
        self.server_url = server_url
        self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)
        self.connected = False
        self.device_id: Optional[str] = None

        # Callbacks
        self.on_sdp_offer: Optional[Callable] = None
        self.on_sdp_answer: Optional[Callable] = None
        self.on_ice_candidate: Optional[Callable] = None
        self.on_pairing_request: Optional[Callable] = None
        self.on_pairing_accepted: Optional[Callable] = None
        self.on_device_unpaired: Optional[Callable] = None
        self.on_device_status: Optional[Callable] = None

        self._setup_handlers()
        logger.info(f"Signaling client initialized for {server_url}")

    def _setup_handlers(self):
        """Setup WebSocket event handlers."""

        @self.sio.event
        async def connect():
            """Handle connection to signaling server."""
            self.connected = True
            logger.info("Connected to signaling server")

        @self.sio.event
        async def disconnect():
            """Handle disconnection from signaling server."""
            self.connected = False
            logger.warning("Disconnected from signaling server")

        @self.sio.event
        async def connected(data):
            """Handle connected event."""
            logger.info(f"Server says: {data.get('message')}")

        @self.sio.event
        async def register_response(data):
            """Handle registration response."""
            if data.get('success'):
                logger.info(f"Successfully registered: {data.get('message')}")
            else:
                logger.error(f"Registration failed: {data.get('error')}")

        @self.sio.event
        async def sdp_offer(data):
            """Handle incoming SDP offer."""
            from_device = data.get('from_device_id')
            sdp = data.get('sdp')
            logger.info(f"Received SDP offer from {from_device}")
            if self.on_sdp_offer:
                await self.on_sdp_offer(from_device, sdp)

        @self.sio.event
        async def sdp_answer(data):
            """Handle incoming SDP answer."""
            from_device = data.get('from_device_id')
            sdp = data.get('sdp')
            logger.info(f"Received SDP answer from {from_device}")
            if self.on_sdp_answer:
                await self.on_sdp_answer(from_device, sdp)

        @self.sio.event
        async def ice_candidate(data):
            """Handle incoming ICE candidate."""
            from_device = data.get('from_device_id')
            candidate = data.get('candidate')
            logger.debug(f"Received ICE candidate from {from_device}")
            if self.on_ice_candidate:
                await self.on_ice_candidate(from_device, candidate)

        @self.sio.event
        async def pairing_request(data):
            """Handle incoming pairing request."""
            from_device = data.get('from_device_id')
            from_name = data.get('from_device_name')
            from_type = data.get('from_device_type')
            logger.info(f"Received pairing request from {from_name} ({from_device})")
            if self.on_pairing_request:
                await self.on_pairing_request(from_device, from_name, from_type)

        @self.sio.event
        async def pairing_accepted(data):
            """Handle pairing acceptance."""
            device_id = data.get('device_id')
            device_name = data.get('device_name')
            device_type = data.get('device_type')
            logger.info(f"Pairing accepted with {device_name} ({device_id})")
            if self.on_pairing_accepted:
                await self.on_pairing_accepted(device_id, device_name, device_type)

        @self.sio.event
        async def device_unpaired(data):
            """Handle device unpaired."""
            device_id = data.get('device_id')
            logger.info(f"Device unpaired: {device_id}")
            if self.on_device_unpaired:
                await self.on_device_unpaired(device_id)

        @self.sio.event
        async def device_status(data):
            """Handle device status update."""
            device_id = data.get('device_id')
            status = data.get('status')
            logger.info(f"Device {device_id} is now {status}")
            if self.on_device_status:
                await self.on_device_status(device_id, status)

        @self.sio.event
        async def error(data):
            """Handle error message."""
            message = data.get('message', 'Unknown error')
            logger.error(f"Server error: {message}")

    async def connect_to_server(self) -> bool:
        """
        Connect to signaling server.

        Returns:
            bool: True if connected successfully
        """
        try:
            logger.info(f"Connecting to signaling server: {self.server_url}")
            await self.sio.connect(self.server_url)
            await asyncio.sleep(0.5)  # Give time for connection to establish
            return self.connected
        except Exception as e:
            logger.error(f"Failed to connect to signaling server: {e}", exc_info=True)
            return False

    async def disconnect_from_server(self):
        """Disconnect from signaling server."""
        try:
            if self.connected:
                logger.info("Disconnecting from signaling server")
                await self.sio.disconnect()
                self.connected = False
        except Exception as e:
            logger.error(f"Error disconnecting from server: {e}", exc_info=True)

    async def register_device(self, device_id: str, device_name: str, device_type: str) -> bool:
        """
        Register device with signaling server.

        Args:
            device_id: Unique device ID
            device_name: User-friendly device name
            device_type: Device type (Windows/Linux/Mac)

        Returns:
            bool: True if registered successfully
        """
        try:
            self.device_id = device_id
            logger.info(f"Registering device: {device_id} ({device_name})")

            await self.sio.emit('register', {
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type
            })

            return True
        except Exception as e:
            logger.error(f"Failed to register device: {e}", exc_info=True)
            return False

    async def send_sdp_offer(self, to_device_id: str, sdp: Dict[str, Any]):
        """
        Send SDP offer to another device.

        Args:
            to_device_id: Target device ID
            sdp: SDP offer data
        """
        try:
            logger.info(f"Sending SDP offer to {to_device_id}")
            await self.sio.emit('sdp_offer', {
                'to_device_id': to_device_id,
                'sdp': sdp
            })
        except Exception as e:
            logger.error(f"Failed to send SDP offer: {e}", exc_info=True)

    async def send_sdp_answer(self, to_device_id: str, sdp: Dict[str, Any]):
        """
        Send SDP answer to another device.

        Args:
            to_device_id: Target device ID
            sdp: SDP answer data
        """
        try:
            logger.info(f"Sending SDP answer to {to_device_id}")
            await self.sio.emit('sdp_answer', {
                'to_device_id': to_device_id,
                'sdp': sdp
            })
        except Exception as e:
            logger.error(f"Failed to send SDP answer: {e}", exc_info=True)

    async def send_ice_candidate(self, to_device_id: str, candidate: Dict[str, Any]):
        """
        Send ICE candidate to another device.

        Args:
            to_device_id: Target device ID
            candidate: ICE candidate data
        """
        try:
            logger.debug(f"Sending ICE candidate to {to_device_id}")
            await self.sio.emit('ice_candidate', {
                'to_device_id': to_device_id,
                'candidate': candidate
            })
        except Exception as e:
            logger.error(f"Failed to send ICE candidate: {e}", exc_info=True)

    async def send_pairing_request(self, to_device_id: str):
        """
        Send pairing request to another device.

        Args:
            to_device_id: Target device ID
        """
        try:
            logger.info(f"Sending pairing request to {to_device_id}")
            await self.sio.emit('pairing_request', {
                'to_device_id': to_device_id
            })
        except Exception as e:
            logger.error(f"Failed to send pairing request: {e}", exc_info=True)

    async def accept_pairing(self, device_id: str):
        """
        Accept pairing request from another device.

        Args:
            device_id: Device ID to pair with
        """
        try:
            logger.info(f"Accepting pairing from {device_id}")
            await self.sio.emit('pairing_accept', {
                'to_device_id': device_id
            })
        except Exception as e:
            logger.error(f"Failed to accept pairing: {e}", exc_info=True)

    async def unpair_device(self, device_id: str):
        """
        Unpair from another device.

        Args:
            device_id: Device ID to unpair from
        """
        try:
            logger.info(f"Unpairing from {device_id}")
            await self.sio.emit('unpair', {
                'device_id': device_id
            })
        except Exception as e:
            logger.error(f"Failed to unpair device: {e}", exc_info=True)
