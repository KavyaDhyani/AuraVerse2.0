"""Device pairing manager."""
import logging
import asyncio
from typing import Optional, Callable
from .qr_generator import QRGenerator
from .security import Security

logger = logging.getLogger(__name__)

class PairingManager:
    """Manages device pairing process."""

    def __init__(self, device_registry, signaling_client):
        """
        Initialize pairing manager.

        Args:
            device_registry: Local device registry
            signaling_client: Signaling client for communication
        """
        self.device_registry = device_registry
        self.signaling_client = signaling_client
        self.pending_requests: dict = {}
        self.on_pairing_request_callback: Optional[Callable] = None
        self.on_pairing_complete_callback: Optional[Callable] = None

        logger.info("Pairing manager initialized")

    def set_on_pairing_request_callback(self, callback: Callable):
        """Set callback for incoming pairing requests."""
        self.on_pairing_request_callback = callback

    def set_on_pairing_complete_callback(self, callback: Callable):
        """Set callback for completed pairing."""
        self.on_pairing_complete_callback = callback

    def generate_pairing_qr(self, device_id: str, device_name: str, device_type: str,
                           server_url: str, public_key: str) -> dict:
        """
        Generate QR code for this device.

        Args:
            device_id: Our device ID
            device_name: Our device name
            device_type: Our device type
            server_url: Signaling server URL
            public_key: Our public key

        Returns:
            dict: QR code payload
        """
        try:
            payload = QRGenerator.generate_pairing_qr(
                device_id, device_name, device_type, server_url, public_key
            )
            logger.info(f"Generated pairing QR for {device_name}")
            return payload
        except Exception as e:
            logger.error(f"Error generating pairing QR: {e}", exc_info=True)
            raise

    def get_qr_as_ascii(self, payload: dict) -> str:
        """
        Get QR code as ASCII for terminal display.

        Args:
            payload: QR code payload

        Returns:
            str: ASCII QR code
        """
        try:
            return QRGenerator.display_qr_in_terminal(payload)
        except Exception as e:
            logger.error(f"Error getting ASCII QR: {e}", exc_info=True)
            raise

    async def pair_with_qr(self, qr_data_string: str) -> bool:
        """
        Pair with device using QR code data.

        Args:
            qr_data_string: QR code data as JSON string

        Returns:
            bool: True if pairing initiated successfully
        """
        try:
            # Parse QR data
            qr_data = QRGenerator.parse_qr_data(qr_data_string)

            # Validate QR format
            if not QRGenerator.validate_qr_format(qr_data_string):
                logger.error("Invalid QR code format")
                return False

            # Extract device info
            peer_device_id = qr_data['device_id']
            peer_device_name = qr_data['device_name']
            peer_device_type = qr_data['device_type']
            peer_public_key = qr_data['public_key']

            # Store temporarily until accepted
            self.pending_requests[peer_device_id] = {
                'device_id': peer_device_id,
                'device_name': peer_device_name,
                'device_type': peer_device_type,
                'public_key': peer_public_key,
                'direction': 'outgoing'
            }

            # Send pairing request via signaling server
            await self.signaling_client.send_pairing_request(peer_device_id)

            logger.info(f"Sent pairing request to {peer_device_name}")
            return True

        except Exception as e:
            logger.error(f"Error pairing with QR: {e}", exc_info=True)
            return False

    async def handle_pairing_request(self, from_device_id: str, from_device_name: str,
                                    from_device_type: str):
        """
        Handle incoming pairing request.

        Args:
            from_device_id: Requesting device ID
            from_device_name: Requesting device name
            from_device_type: Requesting device type
        """
        try:
            logger.info(f"Received pairing request from {from_device_name}")

            # Store pending request
            self.pending_requests[from_device_id] = {
                'device_id': from_device_id,
                'device_name': from_device_name,
                'device_type': from_device_type,
                'direction': 'incoming'
            }

            # Notify user via callback
            if self.on_pairing_request_callback:
                await self.on_pairing_request_callback(
                    from_device_id, from_device_name, from_device_type
                )

        except Exception as e:
            logger.error(f"Error handling pairing request: {e}", exc_info=True)

    async def accept_pairing(self, device_id: str, public_key: str = "") -> bool:
        """
        Accept pairing request.

        Args:
            device_id: Device ID to pair with
            public_key: Public key (if not already known)

        Returns:
            bool: True if pairing accepted successfully
        """
        try:
            pending = self.pending_requests.get(device_id)
            if not pending:
                logger.error(f"No pending pairing request from {device_id}")
                return False

            # Add to paired devices
            success = await self.device_registry.add_paired_device(
                device_id=pending['device_id'],
                device_name=pending['device_name'],
                device_type=pending['device_type'],
                public_key=public_key or pending.get('public_key', '')
            )

            if not success:
                logger.error(f"Failed to add paired device {device_id}")
                return False

            # Send acceptance via signaling server
            await self.signaling_client.accept_pairing(device_id)

            # Remove from pending
            del self.pending_requests[device_id]

            logger.info(f"Accepted pairing with {pending['device_name']}")

            # Notify callback
            if self.on_pairing_complete_callback:
                await self.on_pairing_complete_callback(device_id, pending['device_name'])

            return True

        except Exception as e:
            logger.error(f"Error accepting pairing: {e}", exc_info=True)
            return False

    async def reject_pairing(self, device_id: str):
        """
        Reject pairing request.

        Args:
            device_id: Device ID to reject
        """
        try:
            if device_id in self.pending_requests:
                del self.pending_requests[device_id]
            logger.info(f"Rejected pairing with {device_id}")
        except Exception as e:
            logger.error(f"Error rejecting pairing: {e}", exc_info=True)

    async def handle_pairing_accepted(self, device_id: str, device_name: str,
                                     device_type: str):
        """
        Handle pairing acceptance from remote device.

        Args:
            device_id: Accepted device ID
            device_name: Accepted device name
            device_type: Accepted device type
        """
        try:
            logger.info(f"Pairing accepted by {device_name}")

            # Get pending request info
            pending = self.pending_requests.get(device_id)
            if pending:
                # Add to paired devices
                await self.device_registry.add_paired_device(
                    device_id=device_id,
                    device_name=device_name,
                    device_type=device_type,
                    public_key=pending.get('public_key', '')
                )

                # Remove from pending
                del self.pending_requests[device_id]

                # Notify callback
                if self.on_pairing_complete_callback:
                    await self.on_pairing_complete_callback(device_id, device_name)

        except Exception as e:
            logger.error(f"Error handling pairing accepted: {e}", exc_info=True)

    async def unpair_device(self, device_id: str) -> bool:
        """
        Unpair from a device.

        Args:
            device_id: Device ID to unpair from

        Returns:
            bool: True if unpaired successfully
        """
        try:
            # Remove from local registry
            success = await self.device_registry.remove_paired_device(device_id)

            if success:
                # Notify signaling server
                await self.signaling_client.unpair_device(device_id)
                logger.info(f"Unpaired device: {device_id}")

            return success

        except Exception as e:
            logger.error(f"Error unpairing device: {e}", exc_info=True)
            return False

    async def get_paired_devices(self) -> list:
        """
        Get list of all paired devices.

        Returns:
            list: List of paired devices
        """
        return await self.device_registry.get_all_paired_devices()
