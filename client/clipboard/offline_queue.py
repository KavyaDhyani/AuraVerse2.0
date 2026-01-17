"""Offline queue manager for pending clipboard syncs."""
import asyncio
import logging
import time
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OfflineQueue:
    """Manages offline clipboard sync queue."""

    def __init__(self, database):
        """
        Initialize offline queue.

        Args:
            database: Database instance for persistence
        """
        self.database = database
        self.max_age_hours = 24
        logger.info("Offline queue initialized")

    async def enqueue_update(self, peer_id: str, content: str, timestamp: float):
        """
        Add clipboard update to queue.

        Args:
            peer_id: Target peer device ID
            content: Clipboard content
            timestamp: Timestamp of the update
        """
        try:
            await self.database.save_offline_queue_item(peer_id, content, timestamp)
            logger.info(f"Queued update for {peer_id}: {len(content)} chars")
        except Exception as e:
            logger.error(f"Error enqueuing update for {peer_id}: {e}", exc_info=True)

    async def get_queued_updates(self, peer_id: str) -> List[Dict]:
        """
        Get all queued updates for a peer.

        Args:
            peer_id: Peer device ID

        Returns:
            list: List of queued updates
        """
        try:
            updates = await self.database.load_offline_queue(peer_id)

            # Filter out old updates
            current_time = time.time()
            max_age_seconds = self.max_age_hours * 3600

            filtered_updates = [
                u for u in updates
                if (current_time - u['timestamp']) < max_age_seconds
            ]

            if len(filtered_updates) < len(updates):
                logger.info(f"Filtered out {len(updates) - len(filtered_updates)} old updates")

            return filtered_updates

        except Exception as e:
            logger.error(f"Error getting queued updates for {peer_id}: {e}", exc_info=True)
            return []

    async def clear_queue(self, peer_id: str):
        """
        Clear all queued updates for a peer.

        Args:
            peer_id: Peer device ID
        """
        try:
            await self.database.clear_offline_queue(peer_id)
            logger.info(f"Cleared queue for {peer_id}")
        except Exception as e:
            logger.error(f"Error clearing queue for {peer_id}: {e}", exc_info=True)

    async def flush_queue(self, peer_id: str, sync_engine, device_id: str, device_name: str):
        """
        Flush queue for a peer (send all queued updates).

        Args:
            peer_id: Peer device ID
            sync_engine: Sync engine to send updates through
            device_id: Our device ID
            device_name: Our device name
        """
        try:
            await sync_engine.retry_offline_syncs(peer_id, device_id, device_name)
        except Exception as e:
            logger.error(f"Error flushing queue for {peer_id}: {e}", exc_info=True)

    def is_peer_offline(self, peer_id: str, device_registry) -> bool:
        """
        Check if peer is offline.

        Args:
            peer_id: Peer device ID
            device_registry: Device registry to check status

        Returns:
            bool: True if peer is offline
        """
        try:
            status = device_registry.get_device_status(peer_id)
            return status != 'online'
        except Exception as e:
            logger.error(f"Error checking if {peer_id} is offline: {e}")
            return True
