"""In-memory device registry for tracking connected devices."""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DeviceRegistry:
    """Manages connected devices and their relationships."""

    def __init__(self):
        """Initialize the device registry."""
        self.devices: Dict[str, dict] = {}
        self.device_to_sid: Dict[str, str] = {}  # device_id -> socket_id
        self.sid_to_device: Dict[str, str] = {}  # socket_id -> device_id
        self.pairing_relationships: Dict[str, set] = {}  # device_id -> set of paired device_ids
        logger.info("Device registry initialized")

    def register_device(self, device_id: str, device_name: str, device_type: str, sid: str) -> bool:
        """Register a new device or update existing device."""
        try:
            self.devices[device_id] = {
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type,
                'status': 'online',
                'connected_at': datetime.utcnow().isoformat(),
                'last_seen': datetime.utcnow().isoformat()
            }
            self.device_to_sid[device_id] = sid
            self.sid_to_device[sid] = device_id

            if device_id not in self.pairing_relationships:
                self.pairing_relationships[device_id] = set()

            logger.info(f"Device registered: {device_id} ({device_name}) - Type: {device_type}")
            return True
        except Exception as e:
            logger.error(f"Error registering device {device_id}: {e}")
            return False

    def unregister_device(self, device_id: str) -> bool:
        """Unregister a device."""
        try:
            if device_id in self.devices:
                self.devices[device_id]['status'] = 'offline'
                self.devices[device_id]['last_seen'] = datetime.utcnow().isoformat()

                sid = self.device_to_sid.get(device_id)
                if sid:
                    del self.device_to_sid[device_id]
                    if sid in self.sid_to_device:
                        del self.sid_to_device[sid]

                logger.info(f"Device unregistered: {device_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unregistering device {device_id}: {e}")
            return False

    def get_device_by_sid(self, sid: str) -> Optional[str]:
        """Get device ID by socket ID."""
        return self.sid_to_device.get(sid)

    def get_sid_by_device(self, device_id: str) -> Optional[str]:
        """Get socket ID by device ID."""
        return self.device_to_sid.get(device_id)

    def get_device_info(self, device_id: str) -> Optional[dict]:
        """Get device information."""
        return self.devices.get(device_id)

    def get_all_devices(self) -> List[dict]:
        """Get all registered devices."""
        return list(self.devices.values())

    def get_online_devices(self) -> List[dict]:
        """Get all online devices."""
        return [d for d in self.devices.values() if d['status'] == 'online']

    def add_pairing(self, device_id_1: str, device_id_2: str) -> bool:
        """Add a pairing relationship between two devices."""
        try:
            if device_id_1 not in self.pairing_relationships:
                self.pairing_relationships[device_id_1] = set()
            if device_id_2 not in self.pairing_relationships:
                self.pairing_relationships[device_id_2] = set()

            self.pairing_relationships[device_id_1].add(device_id_2)
            self.pairing_relationships[device_id_2].add(device_id_1)

            logger.info(f"Pairing added: {device_id_1} <-> {device_id_2}")
            return True
        except Exception as e:
            logger.error(f"Error adding pairing: {e}")
            return False

    def remove_pairing(self, device_id_1: str, device_id_2: str) -> bool:
        """Remove a pairing relationship."""
        try:
            if device_id_1 in self.pairing_relationships:
                self.pairing_relationships[device_id_1].discard(device_id_2)
            if device_id_2 in self.pairing_relationships:
                self.pairing_relationships[device_id_2].discard(device_id_1)

            logger.info(f"Pairing removed: {device_id_1} <-> {device_id_2}")
            return True
        except Exception as e:
            logger.error(f"Error removing pairing: {e}")
            return False

    def get_paired_devices(self, device_id: str) -> List[dict]:
        """Get all devices paired with the given device."""
        paired_ids = self.pairing_relationships.get(device_id, set())
        return [self.devices[did] for did in paired_ids if did in self.devices]

    def is_paired(self, device_id_1: str, device_id_2: str) -> bool:
        """Check if two devices are paired."""
        return device_id_2 in self.pairing_relationships.get(device_id_1, set())
