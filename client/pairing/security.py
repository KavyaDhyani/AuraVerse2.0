"""Security functions for device pairing and encryption."""
import logging
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class Security:
    """Security utilities for device pairing."""

    @staticmethod
    def generate_device_keypair():
        """
        Generate RSA keypair for device.

        Returns:
            tuple: (private_key, public_key) as PEM strings
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Get private key PEM
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            # Get public key PEM
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')

            logger.info("Generated device keypair")
            return private_pem, public_pem

        except Exception as e:
            logger.error(f"Error generating keypair: {e}", exc_info=True)
            raise

    @staticmethod
    def sign_device_id(device_id: str, private_key_pem: str) -> str:
        """
        Sign device ID with private key.

        Args:
            device_id: Device ID to sign
            private_key_pem: Private key PEM string

        Returns:
            str: Base64-encoded signature
        """
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,
                backend=default_backend()
            )

            # Sign device ID
            signature = private_key.sign(
                device_id.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Return base64-encoded signature
            return base64.b64encode(signature).decode('utf-8')

        except Exception as e:
            logger.error(f"Error signing device ID: {e}", exc_info=True)
            raise

    @staticmethod
    def verify_device_signature(device_id: str, signature_b64: str, public_key_pem: str) -> bool:
        """
        Verify device ID signature.

        Args:
            device_id: Device ID
            signature_b64: Base64-encoded signature
            public_key_pem: Public key PEM string

        Returns:
            bool: True if signature is valid
        """
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )

            # Decode signature
            signature = base64.b64decode(signature_b64)

            # Verify signature
            public_key.verify(
                signature,
                device_id.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            return True

        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    @staticmethod
    def hash_device_id(device_id: str) -> str:
        """
        Create one-way hash of device ID.

        Args:
            device_id: Device ID

        Returns:
            str: Hex-encoded hash
        """
        return hashlib.sha256(device_id.encode('utf-8')).hexdigest()

    @staticmethod
    def encrypt_local_data(data: bytes, password: str) -> bytes:
        """
        Encrypt data for local storage.

        Args:
            data: Data to encrypt
            password: Password for encryption

        Returns:
            bytes: Encrypted data
        """
        try:
            # Derive key from password
            key = hashlib.sha256(password.encode('utf-8')).digest()
            key_b64 = base64.urlsafe_b64encode(key)

            # Create Fernet cipher
            f = Fernet(key_b64)

            # Encrypt data
            encrypted = f.encrypt(data)
            return encrypted

        except Exception as e:
            logger.error(f"Error encrypting data: {e}", exc_info=True)
            raise

    @staticmethod
    def decrypt_local_data(encrypted_data: bytes, password: str) -> bytes:
        """
        Decrypt locally stored data.

        Args:
            encrypted_data: Encrypted data
            password: Password for decryption

        Returns:
            bytes: Decrypted data
        """
        try:
            # Derive key from password
            key = hashlib.sha256(password.encode('utf-8')).digest()
            key_b64 = base64.urlsafe_b64encode(key)

            # Create Fernet cipher
            f = Fernet(key_b64)

            # Decrypt data
            decrypted = f.decrypt(encrypted_data)
            return decrypted

        except Exception as e:
            logger.error(f"Error decrypting data: {e}", exc_info=True)
            raise
