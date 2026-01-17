"""Terminal User Interface using Rich."""
import asyncio
import logging
from rich.console import Console
from rich.live import Live
from .screens import Screens
from .handlers import UIHandlers

logger = logging.getLogger(__name__)

class TUI:
    """Terminal User Interface manager."""

    def __init__(self, app_controller):
        """
        Initialize TUI.

        Args:
            app_controller: Main application controller
        """
        self.app = app_controller
        self.console = Console()
        self.screens = Screens()
        self.handlers = UIHandlers()
        self.current_screen = 'home'
        self.running = False

        logger.info("TUI initialized")

    async def start(self):
        """Start the TUI."""
        try:
            self.running = True
            logger.info("Starting TUI")

            # Show initial screen
            self.console.clear()
            await self._render_current_screen()

            # Show instructions
            self.console.print("\n[bold cyan]Commands:[/bold cyan] a=add device, h=history, s=settings, r=refresh, q=quit")
            self.console.print("[yellow]Note: TUI is simplified. Use commands to interact.[/yellow]\n")

            # Keep running until stopped
            await self._main_loop()

        except Exception as e:
            logger.error(f"Error in TUI: {e}", exc_info=True)
            self.screens.display_error(f"TUI error: {e}")
        finally:
            self.running = False

    async def _main_loop(self):
        """Main TUI event loop - simplified."""
        # TUI now just displays once and waits for app to call refresh
        # No auto-refresh to avoid terminal issues
        while self.running:
            try:
                await asyncio.sleep(5)
            except KeyboardInterrupt:
                logger.info("TUI interrupted by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in TUI main loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _render_current_screen(self):
        """Render the current screen."""
        try:
            if self.current_screen == 'home':
                await self._render_home()
            elif self.current_screen == 'add_device':
                await self._render_add_device()
            elif self.current_screen == 'history':
                await self._render_history()
            elif self.current_screen == 'settings':
                await self._render_settings()
        except Exception as e:
            logger.error(f"Error rendering screen: {e}", exc_info=True)

    async def _render_home(self):
        """Render home screen."""
        # Get data from app
        paired_devices = await self.app.device_registry.get_all_paired_devices()
        current_clipboard = self.app.clipboard_monitor.get_current_clipboard() or ""

        stats = {
            'syncs_today': 0,  # Would track this in app
            'total_history': len(await self.app.clipboard_history.get_history(limit=1000)),
            'online_devices': sum(1 for d in paired_devices if d.get('status') == 'online')
        }

        # Render screen
        components = self.screens.render_home_screen(paired_devices, current_clipboard, stats)

        self.console.print(components['header'])
        self.console.print()
        self.console.print(components['devices'])
        self.console.print()
        self.console.print(components['clipboard'])
        self.console.print()
        self.console.print(components['stats'])

    async def _render_add_device(self):
        """Render add device screen with QR code."""
        # Generate QR code
        qr_payload = self.app.pairing_manager.generate_pairing_qr(
            self.app.device_id,
            self.app.config.get('device_name', 'My Device'),
            self.app.config.get('device_type', 'Linux'),
            self.app.config.get('server_url', 'http://localhost:5000'),
            self.app.public_key
        )

        qr_ascii = self.app.pairing_manager.get_qr_as_ascii(qr_payload)

        # Render screen
        components = self.screens.render_add_device_screen(
            qr_ascii,
            self.app.config.get('device_name', 'My Device')
        )

        self.console.print(components['header'])
        self.console.print()
        self.console.print(components['qr_code'])
        self.console.print()
        self.console.print(components['instructions'])

    async def _render_history(self):
        """Render clipboard history screen."""
        history_items = await self.app.clipboard_history.get_history(limit=50)

        components = self.screens.render_history_screen(history_items)

        self.console.print(components['header'])
        self.console.print()
        self.console.print(components['history'])

    async def _render_settings(self):
        """Render settings screen."""
        settings = {
            'device_name': self.app.config.get('device_name', 'Unknown'),
            'device_id': self.app.device_id,
            'server_url': self.app.config.get('server_url', 'Not set'),
            'auto_sync': self.app.config.get('auto_sync', True),
            'history_days': self.app.config.get('history_days', 30)
        }

        components = self.screens.render_settings_screen(settings)

        self.console.print(components['header'])
        self.console.print()
        self.console.print(components['settings'])

    def show_notification(self, message: str, level: str = 'info'):
        """Show notification."""
        if level == 'error':
            self.console.print(f"[bold red]❌ {message}[/bold red]")
        elif level == 'success':
            self.console.print(f"[bold green]✓ {message}[/bold green]")
        else:
            self.console.print(f"[bold blue]ℹ {message}[/bold blue]")

    async def refresh(self):
        """Refresh the current screen."""
        self.console.clear()
        await self._render_current_screen()
        self.console.print("\n[bold cyan]Commands:[/bold cyan] a=add device, h=history, s=settings, r=refresh, q=quit\n")

    def change_screen(self, screen_name: str):
        """Change to different screen."""
        self.current_screen = screen_name
        logger.info(f"Changed to screen: {screen_name}")

    async def stop(self):
        """Stop the TUI."""
        self.running = False
        logger.info("TUI stopped")
