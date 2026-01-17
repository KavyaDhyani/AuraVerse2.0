"""Encryption utilities for local storage."""
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pairing.security import Security

logger = logging.getLogger(__name__)

class Encryption:
    """Handles encryption for local storage."""

    def __init__(self, password: str = None):
        """
        Initialize encryption.

        Args:
            password: Password for encryption (optional)
        """
        self.password = password
        self.enabled = password is not None
        logger.info(f"Encryption initialized (enabled: {self.enabled})")

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data if encryption is enabled.

        Args:
            data: Data to encrypt

        Returns:
            bytes: Encrypted data (or original if encryption disabled)
        """
        if not self.enabled:
            return data

        try:
            return Security.encrypt_local_data(data, self.password)
        except Exception as e:
            logger.error(f"Error encrypting data: {e}", exc_info=True)
            raise

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data if encryption is enabled.

        Args:
            encrypted_data: Encrypted data

        Returns:
            bytes: Decrypted data (or original if encryption disabled)
        """
        if not self.enabled:
            return encrypted_data

        try:
            return Security.decrypt_local_data(encrypted_data, self.password)
        except Exception as e:
            logger.error(f"Error decrypting data: {e}", exc_info=True)
            raise
