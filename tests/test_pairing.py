"""Tests for pairing functionality."""
import unittest
from client.pairing.security import Security
from client.pairing.qr_generator import QRGenerator

class TestPairing(unittest.TestCase):
    """Test pairing components."""

    def test_keypair_generation(self):
        """Test RSA keypair generation."""
        private_key, public_key = Security.generate_device_keypair()
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
        self.assertIn('BEGIN PRIVATE KEY', private_key)
        self.assertIn('BEGIN PUBLIC KEY', public_key)

    def test_device_id_hashing(self):
        """Test device ID hashing."""
        device_id = "test-device-123"
        hash1 = Security.hash_device_id(device_id)
        hash2 = Security.hash_device_id(device_id)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex

    def test_qr_generation(self):
        """Test QR code generation."""
        payload = QRGenerator.generate_pairing_qr(
            "device-123",
            "Test Device",
            "Linux",
            "http://localhost:5000",
            "test-public-key"
        )
        self.assertEqual(payload['device_id'], "device-123")
        self.assertEqual(payload['device_name'], "Test Device")
        self.assertEqual(payload['qr_version'], "1.0")

if __name__ == '__main__':
    unittest.main()
