"""Cross-platform clipboard monitoring."""
import asyncio
import logging
import platform
from typing import Optional, Callable
import pyperclip

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    """Monitors clipboard changes across platforms."""

    def __init__(self, poll_interval: float = 0.5):
        """
        Initialize clipboard monitor.

        Args:
            poll_interval: Time between clipboard checks in seconds
        """
        self.poll_interval = poll_interval
        self.last_content: Optional[str] = None
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.on_change_callback: Optional[Callable] = None
        self.platform = platform.system()

        logger.info(f"Clipboard monitor initialized for {self.platform}")

    def set_on_change_callback(self, callback: Callable):
        """
        Set callback for clipboard changes.

        Args:
            callback: Async function to call when clipboard changes
        """
        self.on_change_callback = callback
        logger.debug("Clipboard change callback registered")

    def get_current_clipboard(self) -> Optional[str]:
        """
        Get current clipboard content.

        Returns:
            str: Clipboard content or None if error
        """
        try:
            content = pyperclip.paste()
            return content if content else None
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
            return None

    def set_clipboard(self, content: str) -> bool:
        """
        Set clipboard content.

        Args:
            content: Content to set

        Returns:
            bool: True if successful
        """
        try:
            pyperclip.copy(content)
            self.last_content = content  # Update to avoid triggering our own change
            logger.debug(f"Clipboard set: {len(content)} chars")
            return True
        except Exception as e:
            logger.error(f"Error setting clipboard: {e}")
            return False

    def is_clipboard_changed(self) -> bool:
        """
        Check if clipboard has changed.

        Returns:
            bool: True if changed
        """
        current = self.get_current_clipboard()
        if current is None:
            return False

        if current != self.last_content:
            return True

        return False

    def should_sync(self, content: Optional[str]) -> bool:
        """
        Determine if content should be synced.

        Args:
            content: Clipboard content

        Returns:
            bool: True if should sync
        """
        # Don't sync empty content
        if not content or len(content.strip()) == 0:
            logger.debug("Skipping empty clipboard content")
            return False

        # Don't sync very small content (likely accidental)
        if len(content) < 2:
            logger.debug("Skipping very small clipboard content")
            return False

        # Don't sync if same as last content
        if content == self.last_content:
            return False

        return True

    async def _monitor_loop(self):
        """Internal monitoring loop."""
        logger.info("Starting clipboard monitoring loop")

        # Get initial clipboard content
        self.last_content = self.get_current_clipboard()

        while self.monitoring:
            try:
                current = self.get_current_clipboard()

                if current is not None and current != self.last_content:
                    logger.info(f"Clipboard changed: {len(current)} chars")

                    if self.should_sync(current):
                        self.last_content = current

                        if self.on_change_callback:
                            await self.on_change_callback(current)
                    else:
                        self.last_content = current

                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info("Clipboard monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in clipboard monitor loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)

    async def start_monitoring(self):
        """Start monitoring clipboard changes."""
        if self.monitoring:
            logger.warning("Clipboard monitoring already active")
            return

        logger.info("Starting clipboard monitoring")
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop monitoring clipboard changes."""
        if not self.monitoring:
            return

        logger.info("Stopping clipboard monitoring")
        self.monitoring = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None

        logger.info("Clipboard monitoring stopped")
