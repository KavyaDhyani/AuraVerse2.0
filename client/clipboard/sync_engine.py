"""Clipboard synchronization engine."""
import asyncio
import logging
import time
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)

class SyncEngine:
    """Manages clipboard synchronization between devices."""

    def __init__(self, webrtc_manager, data_channel_handler, device_registry, offline_queue):
        """
        Initialize sync engine.

        Args:
            webrtc_manager: WebRTC manager instance
            data_channel_handler: Data channel handler instance
            device_registry: Local device registry
            offline_queue: Offline queue manager
        """
        self.webrtc_manager = webrtc_manager
        self.data_channel_handler = data_channel_handler
        self.device_registry = device_registry
        self.offline_queue = offline_queue
        self.sequence_number = 0
        self.last_sync_time: Dict[str, float] = {}
        self.on_sync_callback: Optional[Callable] = None

        logger.info("Sync engine initialized")

    def set_on_sync_callback(self, callback: Callable):
        """Set callback for sync events."""
        self.on_sync_callback = callback

    def _get_next_sequence_number(self) -> int:
        """Get next sequence number."""
        self.sequence_number += 1
        return self.sequence_number

    async def sync_to_peer(self, peer_id: str, clipboard_content: str, device_id: str, device_name: str) -> bool:
        """
        Sync clipboard content to a specific peer.

        Args:
            peer_id: Target peer device ID
            clipboard_content: Content to sync
            device_id: Our device ID
            device_name: Our device name

        Returns:
            bool: True if synced successfully
        """
        try:
            # Check if peer is online and connected
            if not self.webrtc_manager.is_connected(peer_id):
                logger.warning(f"Peer {peer_id} not connected, queuing for later")
                await self.queue_sync_if_offline(peer_id, clipboard_content)
                return False

            # Check if data channel is open
            if not self.data_channel_handler.is_channel_open(peer_id):
                logger.warning(f"Data channel to {peer_id} not open, queuing")
                await self.queue_sync_if_offline(peer_id, clipboard_content)
                return False

            # Prepare metadata
            metadata = {
                'timestamp': time.time(),
                'device_id': device_id,
                'device_name': device_name,
                'sequence_number': self._get_next_sequence_number(),
                'content_type': 'text'
            }

            # Send via data channel
            success = await self.data_channel_handler.send_clipboard_data(
                peer_id, clipboard_content, metadata
            )

            if success:
                self.last_sync_time[peer_id] = time.time()
                logger.info(f"Synced to {peer_id}: {len(clipboard_content)} chars")

                if self.on_sync_callback:
                    await self.on_sync_callback(peer_id, 'sent', len(clipboard_content))

            return success

        except Exception as e:
            logger.error(f"Error syncing to {peer_id}: {e}", exc_info=True)
            return False

    async def sync_to_all_peers(self, clipboard_content: str, device_id: str, device_name: str):
        """
        Sync clipboard content to all paired devices.

        Args:
            clipboard_content: Content to sync
            device_id: Our device ID
            device_name: Our device name
        """
        try:
            paired_devices = await self.device_registry.get_all_paired_devices()

            if not paired_devices:
                logger.debug("No paired devices to sync to")
                return

            logger.info(f"Syncing to {len(paired_devices)} paired devices")

            tasks = []
            for device in paired_devices:
                peer_id = device['device_id']
                task = self.sync_to_peer(peer_id, clipboard_content, device_id, device_name)
                tasks.append(task)

            # Send to all peers concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if r is True)
            logger.info(f"Synced to {success_count}/{len(paired_devices)} devices")

        except Exception as e:
            logger.error(f"Error syncing to all peers: {e}", exc_info=True)

    async def receive_from_peer(self, peer_id: str, content: str, timestamp: float,
                                device_name: str, clipboard_monitor) -> bool:
        """
        Handle incoming clipboard content from peer.

        Args:
            peer_id: Source peer device ID
            content: Clipboard content
            timestamp: Timestamp from sender
            device_name: Sender device name
            clipboard_monitor: Clipboard monitor to update local clipboard

        Returns:
            bool: True if applied successfully
        """
        try:
            logger.info(f"Received clipboard from {device_name}: {len(content)} chars")

            # Check if we should update local clipboard
            if self.should_update_local_clipboard(content, peer_id):
                # Update local clipboard
                success = clipboard_monitor.set_clipboard(content)

                if success:
                    self.last_sync_time[peer_id] = time.time()
                    logger.info(f"Updated local clipboard from {device_name}")

                    if self.on_sync_callback:
                        await self.on_sync_callback(peer_id, 'received', len(content))

                    return True
                else:
                    logger.error(f"Failed to update local clipboard")
                    return False
            else:
                logger.debug("Skipping clipboard update (filtered)")
                return False

        except Exception as e:
            logger.error(f"Error receiving from peer {peer_id}: {e}", exc_info=True)
            return False

    def should_update_local_clipboard(self, content: str, source: str) -> bool:
        """
        Determine if we should update local clipboard.

        Args:
            content: Incoming content
            source: Source device ID

        Returns:
            bool: True if should update
        """
        # Apply filters here
        # For now, accept all content

        if not content or len(content) == 0:
            return False

        return True

    def resolve_conflict(self, local_content: str, remote_content: str,
                        local_time: float, remote_time: float) -> str:
        """
        Resolve clipboard conflict (last-write-wins).

        Args:
            local_content: Local clipboard content
            remote_content: Remote clipboard content
            local_time: Local timestamp
            remote_time: Remote timestamp

        Returns:
            str: Content to use
        """
        # Last-write-wins strategy
        if remote_time > local_time:
            logger.debug("Conflict: remote wins (newer)")
            return remote_content
        else:
            logger.debug("Conflict: local wins (newer)")
            return local_content

    async def queue_sync_if_offline(self, peer_id: str, content: str):
        """
        Queue clipboard sync for offline peer.

        Args:
            peer_id: Target peer device ID
            content: Clipboard content
        """
        try:
            await self.offline_queue.enqueue_update(peer_id, content, time.time())
            logger.info(f"Queued clipboard for offline peer: {peer_id}")
        except Exception as e:
            logger.error(f"Error queuing sync for {peer_id}: {e}", exc_info=True)

    async def retry_offline_syncs(self, peer_id: str, device_id: str, device_name: str):
        """
        Retry syncs for a peer that came online.

        Args:
            peer_id: Peer device ID
            device_id: Our device ID
            device_name: Our device name
        """
        try:
            queued_updates = await self.offline_queue.get_queued_updates(peer_id)

            if not queued_updates:
                logger.debug(f"No queued updates for {peer_id}")
                return

            logger.info(f"Retrying {len(queued_updates)} queued syncs for {peer_id}")

            for update in queued_updates:
                content = update['content']
                success = await self.sync_to_peer(peer_id, content, device_id, device_name)

                if success:
                    await self.offline_queue.clear_queue(peer_id)
                else:
                    logger.warning(f"Failed to sync queued update to {peer_id}")
                    break

                await asyncio.sleep(0.5)  # Small delay between syncs

        except Exception as e:
            logger.error(f"Error retrying offline syncs for {peer_id}: {e}", exc_info=True)

    def apply_filters(self, content: str) -> bool:
        """
        Apply user-configured sync filters.

        Args:
            content: Content to check

        Returns:
            bool: True if content passes filters
        """
        # Implement filters here (size limits, content type, etc.)
        # For now, accept all
        return True
