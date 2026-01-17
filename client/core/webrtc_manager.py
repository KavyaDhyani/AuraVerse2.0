"""WebRTC PeerConnection manager."""
import asyncio
import logging
from typing import Dict, Optional, Callable
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, RTCConfiguration
from aiortc.contrib.media import MediaBlackhole
from .ice_config import get_ice_servers
from .data_channel import DataChannelHandler

logger = logging.getLogger(__name__)

class WebRTCManager:
    """Manages WebRTC peer connections."""

    def __init__(self):
        """Initialize WebRTC manager."""
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.connection_states: Dict[str, str] = {}
        self.data_channel_handler = DataChannelHandler()
        self.ice_servers = get_ice_servers()

        # Callbacks
        self.on_connection_state_change: Optional[Callable] = None

        logger.info("WebRTC manager initialized")

    def create_peer_connection(self, peer_id: str) -> RTCPeerConnection:
        """
        Create a new peer connection.

        Args:
            peer_id: ID of the peer device

        Returns:
            RTCPeerConnection: Created peer connection
        """
        try:
            # Close existing connection if any
            if peer_id in self.peer_connections:
                logger.warning(f"Closing existing connection to {peer_id}")
                asyncio.create_task(self.close_peer_connection(peer_id))

            # Create new peer connection with ICE servers
            pc = RTCPeerConnection(configuration=RTCConfiguration(
                iceServers=self.ice_servers
            ))

            self.peer_connections[peer_id] = pc
            self.connection_states[peer_id] = 'new'

            # Set up connection state monitoring
            @pc.on('connectionstatechange')
            async def on_connection_state_change():
                state = pc.connectionState
                logger.info(f"Connection state changed for {peer_id}: {state}")
                self.connection_states[peer_id] = state

                if self.on_connection_state_change:
                    await self.on_connection_state_change(peer_id, state)

                # Clean up on failed or closed connections
                if state in ['failed', 'closed']:
                    await self.close_peer_connection(peer_id)

            @pc.on('icecandidateerror')
            def on_ice_candidate_error(event):
                logger.warning(f"ICE candidate error for {peer_id}: {event}")

            @pc.on('iceconnectionstatechange')
            async def on_ice_connection_state_change():
                ice_state = pc.iceConnectionState
                logger.debug(f"ICE connection state for {peer_id}: {ice_state}")

            @pc.on('datachannel')
            def on_datachannel(channel):
                logger.info(f"Received data channel from {peer_id}: {channel.label}")
                self.data_channel_handler.handle_data_channel(peer_id, channel)

            logger.info(f"Peer connection created for {peer_id}")
            return pc

        except Exception as e:
            logger.error(f"Error creating peer connection for {peer_id}: {e}", exc_info=True)
            raise

    async def create_offer(self, peer_id: str, signaling_client) -> dict:
        """
        Create SDP offer for a peer.

        Args:
            peer_id: ID of the peer device
            signaling_client: Signaling client to send offer through

        Returns:
            dict: SDP offer
        """
        try:
            logger.info(f"Creating offer for {peer_id}")

            # Get or create peer connection
            pc = self.peer_connections.get(peer_id)
            if not pc:
                pc = self.create_peer_connection(peer_id)

            # Create data channel (as offerer)
            self.data_channel_handler.create_data_channel(pc, peer_id)

            # Create offer
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            self.connection_states[peer_id] = 'connecting'

            # Convert to dict for JSON serialization
            sdp_dict = {
                'type': pc.localDescription.type,
                'sdp': pc.localDescription.sdp
            }

            logger.info(f"Created offer for {peer_id}")

            # Send offer via signaling server
            await signaling_client.send_sdp_offer(peer_id, sdp_dict)

            # Set up ICE candidate handler
            @pc.on('icecandidate')
            async def on_ice_candidate(candidate):
                if candidate:
                    logger.debug(f"Sending ICE candidate to {peer_id}")
                    candidate_dict = {
                        'candidate': candidate.candidate,
                        'sdpMid': candidate.sdpMid,
                        'sdpMLineIndex': candidate.sdpMLineIndex
                    }
                    await signaling_client.send_ice_candidate(peer_id, candidate_dict)

            return sdp_dict

        except Exception as e:
            logger.error(f"Error creating offer for {peer_id}: {e}", exc_info=True)
            raise

    async def handle_offer(self, peer_id: str, sdp_offer: dict, signaling_client):
        """
        Handle incoming SDP offer.

        Args:
            peer_id: ID of the peer device
            sdp_offer: SDP offer data
            signaling_client: Signaling client to send answer through
        """
        try:
            logger.info(f"Handling offer from {peer_id}")

            # Get or create peer connection
            pc = self.peer_connections.get(peer_id)
            if not pc:
                pc = self.create_peer_connection(peer_id)

            # Set remote description
            offer_desc = RTCSessionDescription(
                sdp=sdp_offer['sdp'],
                type=sdp_offer['type']
            )
            await pc.setRemoteDescription(offer_desc)

            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            self.connection_states[peer_id] = 'connecting'

            # Convert to dict
            answer_dict = {
                'type': pc.localDescription.type,
                'sdp': pc.localDescription.sdp
            }

            logger.info(f"Created answer for {peer_id}")

            # Send answer via signaling server
            await signaling_client.send_sdp_answer(peer_id, answer_dict)

            # Set up ICE candidate handler
            @pc.on('icecandidate')
            async def on_ice_candidate(candidate):
                if candidate:
                    logger.debug(f"Sending ICE candidate to {peer_id}")
                    candidate_dict = {
                        'candidate': candidate.candidate,
                        'sdpMid': candidate.sdpMid,
                        'sdpMLineIndex': candidate.sdpMLineIndex
                    }
                    await signaling_client.send_ice_candidate(peer_id, candidate_dict)

        except Exception as e:
            logger.error(f"Error handling offer from {peer_id}: {e}", exc_info=True)
            raise

    async def handle_answer(self, peer_id: str, sdp_answer: dict):
        """
        Handle incoming SDP answer.

        Args:
            peer_id: ID of the peer device
            sdp_answer: SDP answer data
        """
        try:
            logger.info(f"Handling answer from {peer_id}")

            pc = self.peer_connections.get(peer_id)
            if not pc:
                logger.error(f"No peer connection found for {peer_id}")
                return

            # Set remote description
            answer_desc = RTCSessionDescription(
                sdp=sdp_answer['sdp'],
                type=sdp_answer['type']
            )
            await pc.setRemoteDescription(answer_desc)

            logger.info(f"Set remote description for {peer_id}")

        except Exception as e:
            logger.error(f"Error handling answer from {peer_id}: {e}", exc_info=True)
            raise

    async def handle_ice_candidate(self, peer_id: str, candidate_data: dict):
        """
        Handle incoming ICE candidate.

        Args:
            peer_id: ID of the peer device
            candidate_data: ICE candidate data
        """
        try:
            pc = self.peer_connections.get(peer_id)
            if not pc:
                logger.warning(f"No peer connection found for ICE candidate from {peer_id}")
                return

            # Create ICE candidate
            candidate = RTCIceCandidate(
                candidate=candidate_data['candidate'],
                sdpMid=candidate_data.get('sdpMid'),
                sdpMLineIndex=candidate_data.get('sdpMLineIndex')
            )

            await pc.addIceCandidate(candidate)
            logger.debug(f"Added ICE candidate for {peer_id}")

        except Exception as e:
            logger.error(f"Error handling ICE candidate from {peer_id}: {e}", exc_info=True)

    async def wait_for_connection_ready(self, peer_id: str, timeout: float = 30.0) -> bool:
        """
        Wait for peer connection to be ready.

        Args:
            peer_id: ID of the peer device
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if connection is ready, False otherwise
        """
        try:
            logger.info(f"Waiting for connection to {peer_id} to be ready")
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                state = self.connection_states.get(peer_id)

                if state == 'connected':
                    logger.info(f"Connection to {peer_id} is ready")
                    return True
                elif state in ['failed', 'closed']:
                    logger.error(f"Connection to {peer_id} failed")
                    return False

                await asyncio.sleep(0.5)

            logger.warning(f"Connection to {peer_id} timed out")
            return False

        except Exception as e:
            logger.error(f"Error waiting for connection to {peer_id}: {e}", exc_info=True)
            return False

    def get_connection_state(self, peer_id: str) -> str:
        """
        Get connection state for a peer.

        Args:
            peer_id: ID of the peer device

        Returns:
            str: Connection state
        """
        return self.connection_states.get(peer_id, 'disconnected')

    def is_connected(self, peer_id: str) -> bool:
        """
        Check if connected to a peer.

        Args:
            peer_id: ID of the peer device

        Returns:
            bool: True if connected
        """
        return self.connection_states.get(peer_id) == 'connected'

    async def close_peer_connection(self, peer_id: str):
        """
        Close peer connection.

        Args:
            peer_id: ID of the peer device
        """
        try:
            logger.info(f"Closing peer connection to {peer_id}")

            # Close data channel
            self.data_channel_handler.close_channel(peer_id)

            # Close peer connection
            pc = self.peer_connections.get(peer_id)
            if pc:
                await pc.close()
                del self.peer_connections[peer_id]

            # Update state
            self.connection_states[peer_id] = 'closed'

            logger.info(f"Peer connection to {peer_id} closed")

        except Exception as e:
            logger.error(f"Error closing peer connection to {peer_id}: {e}", exc_info=True)

    async def close_all_connections(self):
        """Close all peer connections."""
        logger.info("Closing all peer connections")
        peer_ids = list(self.peer_connections.keys())

        for peer_id in peer_ids:
            await self.close_peer_connection(peer_id)

        self.data_channel_handler.close_all_channels()
        logger.info("All peer connections closed")
