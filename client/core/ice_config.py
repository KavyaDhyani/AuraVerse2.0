"""ICE (STUN/TURN) server configuration."""
import logging
from aiortc import RTCIceServer

logger = logging.getLogger(__name__)

# Free STUN servers for NAT traversal
STUN_SERVERS = [
    'stun:stun.l.google.com:19302',
    'stun:stun1.l.google.com:19302',
    'stun:stun2.l.google.com:19302',
    'stun:stun3.l.google.com:19302',
    'stun:stun4.l.google.com:19302',
]

# Additional STUN servers as fallback
FALLBACK_STUN_SERVERS = [
    'stun:stun.services.mozilla.com:3478',
    'stun:stun.twilio.com:3478',
]

def get_ice_servers():
    """
    Get ICE server configuration for WebRTC.

    Returns:
        list: List of RTCIceServer objects
    """
    ice_servers = []

    # Add STUN servers
    for stun_url in STUN_SERVERS:
        ice_servers.append(RTCIceServer(urls=stun_url))

    logger.info(f"Configured {len(ice_servers)} ICE servers")
    return ice_servers

def get_rtc_configuration():
    """
    Get RTCConfiguration for aiortc.

    Returns:
        dict: RTCConfiguration dictionary
    """
    config = {
        'iceServers': get_ice_servers(),
        'iceTransportPolicy': 'all',  # Use all available candidates
        'bundlePolicy': 'balanced',
        'rtcpMuxPolicy': 'require',
    }

    logger.debug(f"RTC Configuration: {config}")
    return config
