"""Basic tests for WebRTC functionality."""
import unittest
import asyncio
from client.core.ice_config import get_ice_servers, get_rtc_configuration

class TestWebRTC(unittest.TestCase):
    """Test WebRTC components."""

    def test_ice_servers_configured(self):
        """Test that ICE servers are configured."""
        ice_servers = get_ice_servers()
        self.assertIsNotNone(ice_servers)
        self.assertGreater(len(ice_servers), 0)
        self.assertTrue(any('stun' in server['urls'] for server in ice_servers))

    def test_rtc_configuration(self):
        """Test RTC configuration."""
        config = get_rtc_configuration()
        self.assertIn('iceServers', config)
        self.assertIn('iceTransportPolicy', config)

if __name__ == '__main__':
    unittest.main()
