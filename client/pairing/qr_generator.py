"""QR code generation and parsing for device pairing."""
import json
import logging
import qrcode
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class QRGenerator:
    """Handles QR code generation and parsing for device pairing."""

    @staticmethod
    def generate_pairing_qr(device_id: str, device_name: str, device_type: str,
                           server_url: str, public_key: str) -> dict:
        """
        Generate QR code data for device pairing.

        Args:
            device_id: Device ID
            device_name: Device name
            device_type: Device type
            server_url: Signaling server URL
            public_key: Device public key

        Returns:
            dict: QR data payload
        """
        try:
            payload = {
                'device_id': device_id,
                'device_name': device_name,
                'device_type': device_type,
                'server_url': server_url,
                'public_key': public_key,
                'qr_version': '1.0'
            }

            logger.info(f"Generated pairing QR payload for {device_name}")
            return payload

        except Exception as e:
            logger.error(f"Error generating pairing QR: {e}", exc_info=True)
            raise

    @staticmethod
    def get_qr_as_image(payload: dict) -> Image:
        """
        Create QR code image from payload.

        Args:
            payload: QR data payload

        Returns:
            PIL.Image: QR code image
        """
        try:
            # Convert payload to JSON string
            data = json.dumps(payload)

            # Generate QR code
            qr = qrcode.QRCode(
                version=None,  # Auto-size
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            logger.debug("Created QR code image")
            return img

        except Exception as e:
            logger.error(f"Error creating QR image: {e}", exc_info=True)
            raise

    @staticmethod
    def display_qr_in_terminal(payload: dict) -> str:
        """
        Generate ASCII QR code for terminal display.

        Args:
            payload: QR data payload

        Returns:
            str: ASCII representation of QR code
        """
        try:
            # Convert payload to JSON string
            data = json.dumps(payload)

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=1,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Get matrix
            matrix = qr.get_matrix()

            # Convert to ASCII (using unicode blocks for better display)
            ascii_qr = []
            for row in matrix:
                line = ''
                for cell in row:
                    line += '██' if cell else '  '
                ascii_qr.append(line)

            logger.debug("Created ASCII QR code")
            return '\n'.join(ascii_qr)

        except Exception as e:
            logger.error(f"Error creating ASCII QR: {e}", exc_info=True)
            raise

    @staticmethod
    def parse_qr_data(qr_string: str) -> dict:
        """
        Parse QR code data string.

        Args:
            qr_string: QR code data as JSON string

        Returns:
            dict: Parsed QR data
        """
        try:
            data = json.loads(qr_string)

            # Validate required fields
            required_fields = ['device_id', 'device_name', 'device_type',
                             'server_url', 'public_key', 'qr_version']

            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            logger.info(f"Parsed QR data for device: {data['device_name']}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid QR data format: {e}")
            raise ValueError("Invalid QR code data format")
        except Exception as e:
            logger.error(f"Error parsing QR data: {e}", exc_info=True)
            raise

    @staticmethod
    def validate_qr_format(qr_string: str) -> bool:
        """
        Validate QR code format.

        Args:
            qr_string: QR code data string

        Returns:
            bool: True if valid
        """
        try:
            data = QRGenerator.parse_qr_data(qr_string)

            # Check version
            if data.get('qr_version') != '1.0':
                logger.warning(f"Unsupported QR version: {data.get('qr_version')}")
                return False

            return True

        except Exception as e:
            logger.debug(f"QR validation failed: {e}")
            return False
