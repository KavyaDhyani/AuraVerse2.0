"""WebSocket message handlers for signaling server."""
import logging
from flask_socketio import emit
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SignalingHandlers:
    """Handle WebSocket messages for signaling."""

    def __init__(self, socketio, registry):
        """Initialize handlers with socketio instance and device registry."""
        self.socketio = socketio
        self.registry = registry

    def handle_register(self, data: Dict[str, Any], sid: str) -> Dict[str, Any]:
        """Handle device registration."""
        try:
            device_id = data.get('device_id')
            device_name = data.get('device_name')
            device_type = data.get('device_type')

            if not all([device_id, device_name, device_type]):
                logger.warning(f"Invalid registration data from {sid}")
                return {'success': False, 'error': 'Missing required fields'}

            success = self.registry.register_device(device_id, device_name, device_type, sid)

            if success:
                # Notify paired devices that this device is online
                self.broadcast_device_status(device_id, 'online')

                return {
                    'success': True,
                    'device_id': device_id,
                    'message': 'Device registered successfully'
                }
            else:
                return {'success': False, 'error': 'Registration failed'}

        except Exception as e:
            logger.error(f"Error in handle_register: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def handle_get_devices(self, data: Dict[str, Any], sid: str) -> Dict[str, Any]:
        """Handle request for device list."""
        try:
            device_id = self.registry.get_device_by_sid(sid)
            if not device_id:
                return {'success': False, 'error': 'Device not registered'}

            # Return only paired devices
            paired_devices = self.registry.get_paired_devices(device_id)

            return {
                'success': True,
                'devices': paired_devices
            }
        except Exception as e:
            logger.error(f"Error in handle_get_devices: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def handle_sdp_offer(self, data: Dict[str, Any], sid: str):
        """Forward SDP offer to target device."""
        try:
            from_device = self.registry.get_device_by_sid(sid)
            to_device = data.get('to_device_id')
            sdp = data.get('sdp')

            if not all([from_device, to_device, sdp]):
                logger.warning(f"Invalid SDP offer from {sid}")
                emit('error', {'message': 'Invalid SDP offer'}, room=sid)
                return

            # Check if devices are paired
            if not self.registry.is_paired(from_device, to_device):
                logger.warning(f"SDP offer between unpaired devices: {from_device} -> {to_device}")
                emit('error', {'message': 'Devices not paired'}, room=sid)
                return

            target_sid = self.registry.get_sid_by_device(to_device)
            if target_sid:
                logger.info(f"Forwarding SDP offer: {from_device} -> {to_device}")
                emit('sdp_offer', {
                    'from_device_id': from_device,
                    'sdp': sdp
                }, room=target_sid)
            else:
                logger.warning(f"Target device {to_device} not connected")
                emit('error', {'message': 'Target device not online'}, room=sid)

        except Exception as e:
            logger.error(f"Error in handle_sdp_offer: {e}", exc_info=True)
            emit('error', {'message': str(e)}, room=sid)

    def handle_sdp_answer(self, data: Dict[str, Any], sid: str):
        """Forward SDP answer to target device."""
        try:
            from_device = self.registry.get_device_by_sid(sid)
            to_device = data.get('to_device_id')
            sdp = data.get('sdp')

            if not all([from_device, to_device, sdp]):
                logger.warning(f"Invalid SDP answer from {sid}")
                emit('error', {'message': 'Invalid SDP answer'}, room=sid)
                return

            target_sid = self.registry.get_sid_by_device(to_device)
            if target_sid:
                logger.info(f"Forwarding SDP answer: {from_device} -> {to_device}")
                emit('sdp_answer', {
                    'from_device_id': from_device,
                    'sdp': sdp
                }, room=target_sid)
            else:
                logger.warning(f"Target device {to_device} not connected")
                emit('error', {'message': 'Target device not online'}, room=sid)

        except Exception as e:
            logger.error(f"Error in handle_sdp_answer: {e}", exc_info=True)
            emit('error', {'message': str(e)}, room=sid)

    def handle_ice_candidate(self, data: Dict[str, Any], sid: str):
        """Forward ICE candidate to target device."""
        try:
            from_device = self.registry.get_device_by_sid(sid)
            to_device = data.get('to_device_id')
            candidate = data.get('candidate')

            if not all([from_device, to_device, candidate]):
                return

            target_sid = self.registry.get_sid_by_device(to_device)
            if target_sid:
                logger.debug(f"Forwarding ICE candidate: {from_device} -> {to_device}")
                emit('ice_candidate', {
                    'from_device_id': from_device,
                    'candidate': candidate
                }, room=target_sid)

        except Exception as e:
            logger.error(f"Error in handle_ice_candidate: {e}", exc_info=True)

    def handle_pairing_request(self, data: Dict[str, Any], sid: str):
        """Handle pairing request between devices."""
        try:
            from_device = self.registry.get_device_by_sid(sid)
            to_device = data.get('to_device_id')

            if not all([from_device, to_device]):
                emit('error', {'message': 'Invalid pairing request'}, room=sid)
                return

            target_sid = self.registry.get_sid_by_device(to_device)
            if target_sid:
                logger.info(f"Pairing request: {from_device} -> {to_device}")
                from_device_info = self.registry.get_device_info(from_device)
                emit('pairing_request', {
                    'from_device_id': from_device,
                    'from_device_name': from_device_info.get('device_name'),
                    'from_device_type': from_device_info.get('device_type')
                }, room=target_sid)
            else:
                emit('error', {'message': 'Target device not online'}, room=sid)

        except Exception as e:
            logger.error(f"Error in handle_pairing_request: {e}", exc_info=True)
            emit('error', {'message': str(e)}, room=sid)

    def handle_pairing_accept(self, data: Dict[str, Any], sid: str):
        """Handle pairing acceptance."""
        try:
            from_device = self.registry.get_device_by_sid(sid)
            to_device = data.get('to_device_id')

            if not all([from_device, to_device]):
                emit('error', {'message': 'Invalid pairing acceptance'}, room=sid)
                return

            # Add pairing relationship
            success = self.registry.add_pairing(from_device, to_device)

            if success:
                logger.info(f"Pairing accepted: {from_device} <-> {to_device}")

                # Notify both devices
                from_device_info = self.registry.get_device_info(from_device)
                to_device_info = self.registry.get_device_info(to_device)

                target_sid = self.registry.get_sid_by_device(to_device)
                if target_sid:
                    emit('pairing_accepted', {
                        'device_id': from_device,
                        'device_name': from_device_info.get('device_name'),
                        'device_type': from_device_info.get('device_type')
                    }, room=target_sid)

                emit('pairing_accepted', {
                    'device_id': to_device,
                    'device_name': to_device_info.get('device_name'),
                    'device_type': to_device_info.get('device_type')
                }, room=sid)
            else:
                emit('error', {'message': 'Pairing failed'}, room=sid)

        except Exception as e:
            logger.error(f"Error in handle_pairing_accept: {e}", exc_info=True)
            emit('error', {'message': str(e)}, room=sid)

    def handle_unpair(self, data: Dict[str, Any], sid: str):
        """Handle device unpairing."""
        try:
            from_device = self.registry.get_device_by_sid(sid)
            to_device = data.get('device_id')

            if not all([from_device, to_device]):
                emit('error', {'message': 'Invalid unpair request'}, room=sid)
                return

            success = self.registry.remove_pairing(from_device, to_device)

            if success:
                logger.info(f"Devices unpaired: {from_device} <-> {to_device}")

                # Notify both devices
                target_sid = self.registry.get_sid_by_device(to_device)
                if target_sid:
                    emit('device_unpaired', {'device_id': from_device}, room=target_sid)

                emit('device_unpaired', {'device_id': to_device}, room=sid)
            else:
                emit('error', {'message': 'Unpair failed'}, room=sid)

        except Exception as e:
            logger.error(f"Error in handle_unpair: {e}", exc_info=True)
            emit('error', {'message': str(e)}, room=sid)

    def handle_disconnect(self, sid: str):
        """Handle device disconnection."""
        try:
            device_id = self.registry.get_device_by_sid(sid)
            if device_id:
                logger.info(f"Device disconnected: {device_id}")
                self.registry.unregister_device(device_id)
                self.broadcast_device_status(device_id, 'offline')
        except Exception as e:
            logger.error(f"Error in handle_disconnect: {e}", exc_info=True)

    def broadcast_device_status(self, device_id: str, status: str):
        """Broadcast device status to all paired devices."""
        try:
            paired_devices = self.registry.get_paired_devices(device_id)
            for device in paired_devices:
                target_sid = self.registry.get_sid_by_device(device['device_id'])
                if target_sid:
                    emit('device_status', {
                        'device_id': device_id,
                        'status': status
                    }, room=target_sid)
        except Exception as e:
            logger.error(f"Error broadcasting device status: {e}", exc_info=True)
