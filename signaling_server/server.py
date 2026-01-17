"""Flask WebSocket signaling server for clipboard sync."""
import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from device_registry import DeviceRegistry
from handlers import SignalingHandlers
from config import Config

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins=Config.CORS_ALLOWED_ORIGINS,
    logger=Config.DEBUG,
    engineio_logger=Config.DEBUG,
    async_mode='threading'
)

# Initialize device registry and handlers
registry = DeviceRegistry()
handlers = SignalingHandlers(socketio, registry)

# HTTP Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'online_devices': len(registry.get_online_devices())
    })

@app.route('/register', methods=['POST'])
def register_device():
    """HTTP endpoint for device registration (backup)."""
    try:
        data = request.json
        device_id = data.get('device_id')
        device_name = data.get('device_name')
        device_type = data.get('device_type')

        if not all([device_id, device_name, device_type]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Note: HTTP registration doesn't create socket connection
        logger.info(f"HTTP registration attempt for {device_id}")
        return jsonify({
            'success': True,
            'message': 'Please connect via WebSocket for full functionality'
        })
    except Exception as e:
        logger.error(f"Error in HTTP register: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/devices', methods=['GET'])
def get_devices():
    """Get list of online devices."""
    try:
        devices = registry.get_online_devices()
        return jsonify({'success': True, 'devices': devices})
    except Exception as e:
        logger.error(f"Error in get_devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to signaling server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")
    handlers.handle_disconnect(request.sid)

@socketio.on('register')
def handle_register(data):
    """Handle device registration."""
    logger.info(f"Registration request from {request.sid}")
    response = handlers.handle_register(data, request.sid)
    emit('register_response', response)

@socketio.on('get_devices')
def handle_get_devices(data):
    """Handle request for device list."""
    response = handlers.handle_get_devices(data, request.sid)
    emit('devices_list', response)

@socketio.on('sdp_offer')
def handle_sdp_offer(data):
    """Handle SDP offer."""
    handlers.handle_sdp_offer(data, request.sid)

@socketio.on('sdp_answer')
def handle_sdp_answer(data):
    """Handle SDP answer."""
    handlers.handle_sdp_answer(data, request.sid)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    """Handle ICE candidate."""
    handlers.handle_ice_candidate(data, request.sid)

@socketio.on('pairing_request')
def handle_pairing_request(data):
    """Handle pairing request."""
    handlers.handle_pairing_request(data, request.sid)

@socketio.on('pairing_accept')
def handle_pairing_accept(data):
    """Handle pairing acceptance."""
    handlers.handle_pairing_accept(data, request.sid)

@socketio.on('unpair')
def handle_unpair(data):
    """Handle device unpairing."""
    handlers.handle_unpair(data, request.sid)

@socketio.on_error_default
def default_error_handler(e):
    """Handle errors."""
    logger.error(f"SocketIO error: {e}", exc_info=True)
    emit('error', {'message': 'An error occurred'})

def initialize_server():
    """Initialize and start the signaling server."""
    logger.info("=" * 60)
    logger.info("Universal Clipboard Sync - Signaling Server")
    logger.info("=" * 60)
    logger.info(f"Host: {Config.HOST}")
    logger.info(f"Port: {Config.PORT}")
    logger.info(f"Debug: {Config.DEBUG}")
    logger.info("=" * 60)

    try:
        socketio.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    initialize_server()
