"""Client configuration management."""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Config:
    """Manages client configuration."""

    DEFAULT_CONFIG = {
        'device_name': 'My Device',
        'device_type': 'Linux',
        'server_url': 'http://localhost:5000',
        'auto_sync': True,
        'history_days': 30,
        'poll_interval': 0.5,
        'debug': False
    }

    def __init__(self, config_path: str = None):
        """
        Initialize config.

        Args:
            config_path: Path to config file
        """
        if config_path is None:
            home = Path.home()
            config_dir = home / '.clipboard-sync'
            config_dir.mkdir(exist_ok=True)
            config_path = str(config_dir / 'config.json')

        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        logger.info(f"Config initialized at: {config_path}")

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            dict: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info("Configuration loaded from file")
            else:
                self.config = self.DEFAULT_CONFIG.copy()
                self.save()
                logger.info("Created default configuration")

            return self.config

        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            self.config = self.DEFAULT_CONFIG.copy()
            return self.config

    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)

    def get(self, key: str, default=None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        self.save()
        logger.debug(f"Config updated: {key}={value}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration."""
        return self.config.copy()

    def update(self, updates: Dict[str, Any]):
        """
        Update multiple configuration values.

        Args:
            updates: Dictionary of updates
        """
        self.config.update(updates)
        self.save()
        logger.info(f"Config updated with {len(updates)} changes")
