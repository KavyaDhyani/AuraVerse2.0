"""Main entry point for Universal Clipboard Sync client."""
import asyncio
import argparse
import logging
import platform
import sys
import uuid
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from storage.database import Database
from core.signaling_client import SignalingClient
from core.webrtc_manager import WebRTCManager
from clipboard.monitor import ClipboardMonitor
from clipboard.sync_engine import SyncEngine
from clipboard.offline_queue import OfflineQueue
from clipboard.history import ClipboardHistory
from pairing.security import Security
from pairing.device_registry import DeviceRegistry
from pairing.pairing_manager import PairingManager
from ui.tui import TUI

logger = logging.getLogger(__name__)

class ClipboardSyncClient:
    """Main clipboard sync client application."""

    def __init__(self, config_path: str = None, device_name: str = None,
                 server_url: str = None, debug: bool = False, no_tui: bool = False):
        """
        Initialize client application.

        Args:
            config_path: Path to config file
            device_name: Device name override
            server_url: Server URL override
            debug: Enable debug logging
            no_tui: Run without TUI (headless mode)
        """
        self.no_tui = no_tui
        # Setup logging
        log_level = logging.DEBUG if debug else logging.INFO

        # Create log directory if it doesn't exist
        log_dir = Path.home() / '.clipboard-sync'
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_dir / 'client.log')
            ]
        )

        logger.info("="* 60)
        logger.info("Universal Clipboard Sync Client - Starting")
        logger.info("=" * 60)

        # Load configuration
        self.config = Config(config_path)
        self.config.load()

        # Apply overrides
        if device_name:
            self.config.set('device_name', device_name)
        if server_url:
            self.config.set('server_url', server_url)
        if debug:
            self.config.set('debug', True)

        # Generate or load device ID
        if not self.config.get('device_id'):
            device_id = str(uuid.uuid4())
            self.config.set('device_id', device_id)

        self.device_id = self.config.get('device_id')

        # Detect device type if not set
        if not self.config.get('device_type'):
            device_type = platform.system()
            self.config.set('device_type', device_type)

        # Generate keypair if not exists
        if not self.config.get('private_key') or not self.config.get('public_key'):
            logger.info("Generating device keypair...")
            private_key, public_key = Security.generate_device_keypair()
            self.config.set('private_key', private_key)
            self.config.set('public_key', public_key)

        self.private_key = self.config.get('private_key')
        self.public_key = self.config.get('public_key')

        # Initialize components
        self.database = Database()
        self.signaling_client = SignalingClient(self.config.get('server_url'))
        self.webrtc_manager = WebRTCManager()
        self.clipboard_monitor = ClipboardMonitor(self.config.get('poll_interval', 0.5))
        self.device_registry = DeviceRegistry(self.database)
        self.offline_queue = OfflineQueue(self.database)
        self.clipboard_history = ClipboardHistory(self.database)
        self.sync_engine = SyncEngine(
            self.webrtc_manager,
            self.webrtc_manager.data_channel_handler,
            self.device_registry,
            self.offline_queue
        )
        self.pairing_manager = PairingManager(self.device_registry, self.signaling_client)
        self.tui = TUI(self)

        logger.info(f"Device ID: {self.device_id}")
        logger.info(f"Device Name: {self.config.get('device_name')}")
        logger.info(f"Server URL: {self.config.get('server_url')}")

    async def initialize(self):
        """Initialize all components."""
        try:
            logger.info("Initializing components...")

            # Initialize database
            await self.database.initialize_database()

            # Load paired devices
            await self.device_registry.load_devices()

            # Setup callbacks
            self._setup_callbacks()

            logger.info("Components initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing components: {e}", exc_info=True)
            raise

    def _setup_callbacks(self):
        """Setup callbacks between components."""
        # Clipboard monitor callback
        self.clipboard_monitor.set_on_change_callback(self._on_clipboard_change)

        # Data channel message callback
        self.webrtc_manager.data_channel_handler.set_message_callback(self._on_data_channel_message)
        self.webrtc_manager.data_channel_handler.set_open_callback(self._on_data_channel_open)

        # Signaling client callbacks
        self.signaling_client.on_sdp_offer = self._on_sdp_offer
        self.signaling_client.on_sdp_answer = self._on_sdp_answer
        self.signaling_client.on_ice_candidate = self._on_ice_candidate
        self.signaling_client.on_pairing_request = self._on_pairing_request
        self.signaling_client.on_pairing_accepted = self._on_pairing_accepted
        self.signaling_client.on_device_status = self._on_device_status

        # WebRTC connection state callback
        self.webrtc_manager.on_connection_state_change = self._on_connection_state_change

        logger.debug("Callbacks configured")

    async def _on_clipboard_change(self, content: str):
        """Handle local clipboard change."""
        try:
            logger.info(f"Local clipboard changed: {len(content)} chars")

            # Add to history
            import time
            await self.clipboard_history.add_to_history(content, self.device_id, time.time())

            # Sync to all peers
            await self.sync_engine.sync_to_all_peers(
                content,
                self.device_id,
                self.config.get('device_name')
            )

        except Exception as e:
            logger.error(f"Error handling clipboard change: {e}", exc_info=True)

    async def _on_data_channel_message(self, peer_id: str, data: dict):
        """Handle incoming data channel message."""
        try:
            if data.get('type') == 'clipboard_update':
                content = data.get('content')
                metadata = data.get('metadata', {})
                timestamp = metadata.get('timestamp', 0)
                device_name = metadata.get('device_name', 'Unknown')

                logger.info(f"Received clipboard from {device_name}")

                # Add to history
                await self.clipboard_history.add_to_history(content, peer_id, timestamp)

                # Update local clipboard
                await self.sync_engine.receive_from_peer(
                    peer_id, content, timestamp, device_name, self.clipboard_monitor
                )

        except Exception as e:
            logger.error(f"Error handling data channel message: {e}", exc_info=True)

    async def _on_data_channel_open(self, peer_id: str):
        """Handle data channel open."""
        logger.info(f"Data channel opened with {peer_id}")

        # Retry offline syncs
        await self.sync_engine.retry_offline_syncs(
            peer_id,
            self.device_id,
            self.config.get('device_name')
        )

    async def _on_sdp_offer(self, from_device_id: str, sdp: dict):
        """Handle incoming SDP offer."""
        try:
            logger.info(f"Received SDP offer from {from_device_id}")
            await self.webrtc_manager.handle_offer(from_device_id, sdp, self.signaling_client)
        except Exception as e:
            logger.error(f"Error handling SDP offer: {e}", exc_info=True)

    async def _on_sdp_answer(self, from_device_id: str, sdp: dict):
        """Handle incoming SDP answer."""
        try:
            logger.info(f"Received SDP answer from {from_device_id}")
            await self.webrtc_manager.handle_answer(from_device_id, sdp)
        except Exception as e:
            logger.error(f"Error handling SDP answer: {e}", exc_info=True)

    async def _on_ice_candidate(self, from_device_id: str, candidate: dict):
        """Handle incoming ICE candidate."""
        try:
            await self.webrtc_manager.handle_ice_candidate(from_device_id, candidate)
        except Exception as e:
            logger.error(f"Error handling ICE candidate: {e}", exc_info=True)

    async def _on_pairing_request(self, from_device_id: str, from_device_name: str, from_device_type: str):
        """Handle incoming pairing request."""
        try:
            logger.info(f"Pairing request from {from_device_name}")
            await self.pairing_manager.handle_pairing_request(from_device_id, from_device_name, from_device_type)

            # Auto-accept for now (in production, show UI prompt)
            await self.pairing_manager.accept_pairing(from_device_id)

        except Exception as e:
            logger.error(f"Error handling pairing request: {e}", exc_info=True)

    async def _on_pairing_accepted(self, device_id: str, device_name: str, device_type: str):
        """Handle pairing accepted."""
        try:
            logger.info(f"Pairing accepted with {device_name}")
            await self.pairing_manager.handle_pairing_accepted(device_id, device_name, device_type)

            # Initiate WebRTC connection
            await self.webrtc_manager.create_offer(device_id, self.signaling_client)

        except Exception as e:
            logger.error(f"Error handling pairing accepted: {e}", exc_info=True)

    async def _on_device_status(self, device_id: str, status: str):
        """Handle device status change."""
        try:
            logger.info(f"Device {device_id} status: {status}")
            await self.device_registry.update_device_status(device_id, status)

            if status == 'online':
                # Initiate connection if not connected
                if not self.webrtc_manager.is_connected(device_id):
                    await self.webrtc_manager.create_offer(device_id, self.signaling_client)

        except Exception as e:
            logger.error(f"Error handling device status: {e}", exc_info=True)

    async def _on_connection_state_change(self, peer_id: str, state: str):
        """Handle WebRTC connection state change."""
        logger.info(f"Connection to {peer_id}: {state}")
        await self.device_registry.update_device_status(peer_id, state)

    async def connect_to_server(self):
        """Connect to signaling server."""
        try:
            logger.info("Connecting to signaling server...")
            success = await self.signaling_client.connect_to_server()

            if not success:
                logger.error("Failed to connect to signaling server")
                return False

            # Register device
            await self.signaling_client.register_device(
                self.device_id,
                self.config.get('device_name'),
                self.config.get('device_type')
            )

            logger.info("Connected to signaling server")
            return True

        except Exception as e:
            logger.error(f"Error connecting to server: {e}", exc_info=True)
            return False

    async def start(self):
        """Start the client application."""
        try:
            # Initialize components
            await self.initialize()

            # Connect to server
            if not await self.connect_to_server():
                logger.error("Cannot start without server connection")
                return

            # Start clipboard monitoring
            await self.clipboard_monitor.start_monitoring()

            # Start TUI or wait in headless mode
            if self.no_tui:
                logger.info("Running in headless mode (no TUI)")
                logger.info("Press Ctrl+C to stop")
                # Keep running until interrupted
                while True:
                    await asyncio.sleep(1)
            else:
                await self.tui.start()

        except KeyboardInterrupt:
            logger.info("Client interrupted by user")
        except Exception as e:
            logger.error(f"Error starting client: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown the client."""
        try:
            logger.info("Shutting down...")

            # Stop clipboard monitoring
            await self.clipboard_monitor.stop_monitoring()

            # Close all WebRTC connections
            await self.webrtc_manager.close_all_connections()

            # Disconnect from signaling server
            await self.signaling_client.disconnect_from_server()

            logger.info("Shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Universal Clipboard Sync Client')
    parser.add_argument('--device-name', type=str, help='Device name')
    parser.add_argument('--server-url', type=str, help='Signaling server URL')
    parser.add_argument('--config-path', type=str, help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-tui', action='store_true', help='Run without TUI (headless)')

    return parser.parse_args()

async def main():
    """Main entry point."""
    args = parse_arguments()

    client = ClipboardSyncClient(
        config_path=args.config_path,
        device_name=args.device_name,
        server_url=args.server_url,
        debug=args.debug,
        no_tui=args.no_tui
    )

    await client.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)
