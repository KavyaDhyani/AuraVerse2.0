"""Local device registry for paired devices."""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class DeviceRegistry:
    """Manages locally paired devices."""

    def __init__(self, database):
        """
        Initialize device registry.

        Args:
            database: Database instance for storage
        """
        self.database = database
        self.devices_cache: Dict[str, dict] = {}
        logger.info("Device registry initialized")

    async def load_devices(self):
        """Load paired devices from database into cache."""
        try:
            devices = await self.database.load_paired_devices()
            self.devices_cache = {d['device_id']: d for d in devices}
            logger.info(f"Loaded {len(self.devices_cache)} paired devices")
        except Exception as e:
            logger.error(f"Error loading devices: {e}", exc_info=True)

    async def add_paired_device(self, device_id: str, device_name: str,
                               device_type: str, public_key: str) -> bool:
        """
        Add a paired device.

        Args:
            device_id: Device ID
            device_name: Device name
            device_type: Device type
            public_key: Device public key

        Returns:
            bool: True if added successfully
        """
        try:
            import time

            device_info = {
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type,
                'public_key': public_key,
                'date_paired': time.time(),
                'last_seen': time.time(),
                'sync_enabled': True,
                'status': 'offline'
            }

            await self.database.save_paired_device(device_info)
            self.devices_cache[device_id] = device_info

            logger.info(f"Added paired device: {device_name} ({device_id})")
            return True

        except Exception as e:
            logger.error(f"Error adding paired device {device_id}: {e}", exc_info=True)
            return False

    async def remove_paired_device(self, device_id: str) -> bool:
        """
        Remove a paired device.

        Args:
            device_id: Device ID

        Returns:
            bool: True if removed successfully
        """
        try:
            await self.database.delete_paired_device(device_id)

            if device_id in self.devices_cache:
                del self.devices_cache[device_id]

            logger.info(f"Removed paired device: {device_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing paired device {device_id}: {e}", exc_info=True)
            return False

    def get_paired_device(self, device_id: str) -> Optional[dict]:
        """
        Get paired device info.

        Args:
            device_id: Device ID

        Returns:
            dict: Device info or None
        """
        return self.devices_cache.get(device_id)

    async def get_all_paired_devices(self) -> List[dict]:
        """
        Get all paired devices.

        Returns:
            list: List of all paired devices
        """
        return list(self.devices_cache.values())

    async def update_device_status(self, device_id: str, status: str):
        """
        Update device online/offline status.

        Args:
            device_id: Device ID
            status: Status (online/offline/connecting)
        """
        try:
            import time

            if device_id in self.devices_cache:
                self.devices_cache[device_id]['status'] = status
                self.devices_cache[device_id]['last_seen'] = time.time()

                # Update in database
                await self.database.update_device_status(device_id, status)

                logger.debug(f"Updated device {device_id} status to {status}")

        except Exception as e:
            logger.error(f"Error updating device status: {e}", exc_info=True)

    def get_device_status(self, device_id: str) -> str:
        """
        Get device status.

        Args:
            device_id: Device ID

        Returns:
            str: Status (online/offline/connecting)
        """
        device = self.devices_cache.get(device_id)
        return device['status'] if device else 'offline'

    def is_device_trusted(self, device_id: str) -> bool:
        """
        Check if device is in paired list.

        Args:
            device_id: Device ID

        Returns:
            bool: True if device is paired
        """
        return device_id in self.devices_cache

    async def set_sync_enabled(self, device_id: str, enabled: bool):
        """
        Enable/disable sync for a device.

        Args:
            device_id: Device ID
            enabled: Whether sync is enabled
        """
        try:
            if device_id in self.devices_cache:
                self.devices_cache[device_id]['sync_enabled'] = enabled
                await self.database.update_device_sync_enabled(device_id, enabled)
                logger.info(f"Set sync_enabled={enabled} for {device_id}")
        except Exception as e:
            logger.error(f"Error setting sync enabled: {e}", exc_info=True)

    def is_sync_enabled(self, device_id: str) -> bool:
        """
        Check if sync is enabled for a device.

        Args:
            device_id: Device ID

        Returns:
            bool: True if sync enabled
        """
        device = self.devices_cache.get(device_id)
        return device.get('sync_enabled', True) if device else False
