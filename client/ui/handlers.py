"""User input handlers for TUI."""
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class UIHandlers:
    """Handles user input and actions in TUI."""

    def __init__(self):
        """Initialize UI handlers."""
        self.on_add_device_callback: Optional[Callable] = None
        self.on_remove_device_callback: Optional[Callable] = None
        self.on_view_history_callback: Optional[Callable] = None
        self.on_settings_callback: Optional[Callable] = None
        self.on_quit_callback: Optional[Callable] = None

        logger.info("UI handlers initialized")

    def set_callbacks(self, **callbacks):
        """Set callbacks for various actions."""
        for name, callback in callbacks.items():
            setattr(self, f"on_{name}_callback", callback)

    async def handle_key_input(self, key: str) -> Optional[str]:
        """
        Handle keyboard input.

        Args:
            key: Key pressed

        Returns:
            str: Action to take or None
        """
        key_lower = key.lower()

        if key_lower == 'q':
            logger.info("User requested quit")
            if self.on_quit_callback:
                await self.on_quit_callback()
            return 'quit'

        elif key_lower == 'a':
            logger.info("User requested add device")
            if self.on_add_device_callback:
                await self.on_add_device_callback()
            return 'add_device'

        elif key_lower == 'r':
            logger.info("User requested remove device")
            if self.on_remove_device_callback:
                await self.on_remove_device_callback()
            return 'remove_device'

        elif key_lower == 'h':
            logger.info("User requested view history")
            if self.on_view_history_callback:
                await self.on_view_history_callback()
            return 'view_history'

        elif key_lower == 's':
            logger.info("User requested settings")
            if self.on_settings_callback:
                await self.on_settings_callback()
            return 'settings'

        elif key_lower == '?':
            return 'help'

        return None

    async def handle_add_device(self):
        """Handle add device action."""
        logger.debug("Handling add device")
        if self.on_add_device_callback:
            await self.on_add_device_callback()

    async def handle_remove_device(self, device_id: str):
        """Handle remove device action."""
        logger.debug(f"Handling remove device: {device_id}")
        if self.on_remove_device_callback:
            await self.on_remove_device_callback(device_id)

    async def handle_settings_change(self, key: str, value: any):
        """Handle settings change."""
        logger.debug(f"Handling settings change: {key}={value}")
        # Implementation would update config

    def show_notification(self, message: str, level: str = 'info'):
        """Show notification message."""
        if level == 'error':
            logger.error(f"Notification: {message}")
        elif level == 'warning':
            logger.warning(f"Notification: {message}")
        else:
            logger.info(f"Notification: {message}")

    def confirm_action(self, message: str) -> bool:
        """Show confirmation dialog."""
        # In a real TUI, this would show a dialog
        logger.info(f"Confirmation: {message}")
        return True
