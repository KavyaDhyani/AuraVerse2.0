"""Clipboard history manager."""
import logging
import time
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ClipboardHistory:
    """Manages local clipboard history."""

    def __init__(self, database):
        """
        Initialize clipboard history.

        Args:
            database: Database instance for storage
        """
        self.database = database
        logger.info("Clipboard history initialized")

    async def add_to_history(self, content: str, source_device: str, timestamp: float):
        """
        Add item to clipboard history.

        Args:
            content: Clipboard content
            source_device: Source device ID
            timestamp: Timestamp of the clipboard event
        """
        try:
            await self.database.save_clipboard_item(content, source_device, timestamp)
            logger.debug(f"Added to history from {source_device}: {len(content)} chars")
        except Exception as e:
            logger.error(f"Error adding to history: {e}", exc_info=True)

    async def get_history(self, limit: int = 50) -> List[Dict]:
        """
        Get recent clipboard history.

        Args:
            limit: Maximum number of items to return

        Returns:
            list: List of clipboard history items
        """
        try:
            history = await self.database.load_clipboard_history(limit)
            logger.debug(f"Retrieved {len(history)} history items")
            return history
        except Exception as e:
            logger.error(f"Error getting history: {e}", exc_info=True)
            return []

    async def search_history(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search clipboard history.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            list: Matching clipboard history items
        """
        try:
            history = await self.get_history(limit=200)

            # Simple text search
            query_lower = query.lower()
            results = [
                item for item in history
                if query_lower in item['content'].lower()
            ]

            logger.debug(f"Search '{query}' found {len(results)} results")
            return results[:limit]

        except Exception as e:
            logger.error(f"Error searching history: {e}", exc_info=True)
            return []

    async def clear_history(self):
        """Clear all clipboard history."""
        try:
            await self.database.clear_clipboard_history()
            logger.info("Clipboard history cleared")
        except Exception as e:
            logger.error(f"Error clearing history: {e}", exc_info=True)

    async def get_history_by_device(self, device_id: str, limit: int = 20) -> List[Dict]:
        """
        Get clipboard history from specific device.

        Args:
            device_id: Device ID to filter by
            limit: Maximum number of items

        Returns:
            list: Clipboard history items from device
        """
        try:
            history = await self.get_history(limit=200)

            device_history = [
                item for item in history
                if item.get('source_device_id') == device_id
            ]

            logger.debug(f"Retrieved {len(device_history)} history items from {device_id}")
            return device_history[:limit]

        except Exception as e:
            logger.error(f"Error getting history by device: {e}", exc_info=True)
            return []

    async def export_history(self, format: str = 'json') -> Optional[str]:
        """
        Export clipboard history.

        Args:
            format: Export format (currently only 'json')

        Returns:
            str: Exported history data
        """
        try:
            import json

            history = await self.get_history(limit=1000)

            if format == 'json':
                return json.dumps(history, indent=2)
            else:
                logger.warning(f"Unsupported export format: {format}")
                return None

        except Exception as e:
            logger.error(f"Error exporting history: {e}", exc_info=True)
            return None
