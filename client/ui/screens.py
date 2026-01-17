"""TUI screen components using Rich library."""
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

class Screens:
    """TUI screen renderer using Rich."""

    def __init__(self):
        """Initialize screens."""
        self.console = Console()
        logger.info("Screens initialized")

    def render_home_screen(self, paired_devices: List[Dict], current_clipboard: str,
                          stats: Dict) -> Layout:
        """
        Render home/dashboard screen.

        Args:
            paired_devices: List of paired devices
            current_clipboard: Current clipboard preview
            stats: Statistics dict

        Returns:
            Layout: Screen layout
        """
        layout = Layout()

        # Create header
        header = Panel(
            "[bold cyan]Universal Clipboard Sync[/bold cyan]\n"
            "[dim]Press 'a' to add device, 'r' to remove, 'h' for history, 's' for settings, 'q' to quit[/dim]",
            style="cyan"
        )

        # Device list table
        device_table = self._create_device_table(paired_devices)

        # Clipboard preview
        clipboard_text = current_clipboard[:100] if current_clipboard else "(empty)"
        clipboard_panel = Panel(
            f"[yellow]{clipboard_text}[/yellow]",
            title="Current Clipboard",
            border_style="yellow"
        )

        # Stats
        stats_text = f"""
Syncs Today: {stats.get('syncs_today', 0)}
Total History: {stats.get('total_history', 0)}
Online Devices: {stats.get('online_devices', 0)}/{len(paired_devices)}
        """
        stats_panel = Panel(stats_text.strip(), title="Statistics", border_style="green")

        return {
            'header': header,
            'devices': device_table,
            'clipboard': clipboard_panel,
            'stats': stats_panel
        }

    def _create_device_table(self, devices: List[Dict]) -> Table:
        """Create device list table."""
        table = Table(title="Paired Devices", show_header=True, header_style="bold magenta")

        table.add_column("Status", style="dim", width=8)
        table.add_column("Device Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Last Sync", style="yellow")

        for device in devices:
            # Status indicator
            status = device.get('status', 'offline')
            if status == 'online':
                status_icon = "🟢 Online"
                status_style = "green"
            elif status == 'connecting':
                status_icon = "⏳ Connecting"
                status_style = "yellow"
            else:
                status_icon = "🔴 Offline"
                status_style = "red"

            # Last sync time
            last_seen = device.get('last_seen', 0)
            if last_seen:
                time_ago = self._format_time_ago(last_seen)
            else:
                time_ago = "never"

            table.add_row(
                f"[{status_style}]{status_icon}[/{status_style}]",
                device['device_name'],
                device['device_type'],
                time_ago
            )

        if not devices:
            table.add_row("[dim]No paired devices[/dim]", "", "", "")

        return table

    def render_add_device_screen(self, qr_code: str, device_name: str) -> Dict:
        """
        Render add device screen with QR code.

        Args:
            qr_code: ASCII QR code
            device_name: This device's name

        Returns:
            dict: Screen components
        """
        header = Panel(
            f"[bold cyan]Pair New Device[/bold cyan]\n"
            f"[dim]Scan this QR code from another device running Clipboard Sync[/dim]",
            style="cyan"
        )

        qr_panel = Panel(
            qr_code,
            title=f"QR Code for {device_name}",
            border_style="green"
        )

        instructions = Panel(
            "[yellow]Instructions:[/yellow]\n"
            "1. Open Clipboard Sync on another device\n"
            "2. Press 'a' to add device\n"
            "3. Scan this QR code\n"
            "4. Accept the pairing request\n\n"
            "[dim]Press 'q' to go back[/dim]",
            title="How to Pair",
            border_style="blue"
        )

        return {
            'header': header,
            'qr_code': qr_panel,
            'instructions': instructions
        }

    def render_history_screen(self, history_items: List[Dict]) -> Dict:
        """
        Render clipboard history screen.

        Args:
            history_items: List of history items

        Returns:
            dict: Screen components
        """
        header = Panel(
            "[bold cyan]Clipboard History[/bold cyan]\n"
            "[dim]Press 'q' to go back[/dim]",
            style="cyan"
        )

        history_table = Table(title="Recent Clipboard Items", show_header=True)
        history_table.add_column("Time", style="dim", width=20)
        history_table.add_column("Source", style="cyan", width=20)
        history_table.add_column("Content", style="white")

        for item in history_items[:20]:  # Show last 20
            timestamp = datetime.fromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            source = item.get('source_device_id', 'Unknown')[:20]
            content = item['content'][:60] + ('...' if len(item['content']) > 60 else '')

            history_table.add_row(timestamp, source, content)

        if not history_items:
            history_table.add_row("[dim]No history items[/dim]", "", "")

        return {
            'header': header,
            'history': history_table
        }

    def render_settings_screen(self, settings: Dict) -> Dict:
        """
        Render settings screen.

        Args:
            settings: Current settings

        Returns:
            dict: Screen components
        """
        header = Panel(
            "[bold cyan]Settings[/bold cyan]\n"
            "[dim]Press 'q' to go back[/dim]",
            style="cyan"
        )

        settings_text = f"""
Device Name: {settings.get('device_name', 'Unknown')}
Device ID: {settings.get('device_id', 'Unknown')[:20]}...
Server URL: {settings.get('server_url', 'Not set')}
Auto-sync: {'Enabled' if settings.get('auto_sync', True) else 'Disabled'}
History Retention: {settings.get('history_days', 30)} days
        """

        settings_panel = Panel(
            settings_text.strip(),
            title="Current Settings",
            border_style="green"
        )

        return {
            'header': header,
            'settings': settings_panel
        }

    def _format_time_ago(self, timestamp: float) -> str:
        """Format timestamp as time ago string."""
        import time
        diff = time.time() - timestamp

        if diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff/60)}m ago"
        elif diff < 86400:
            return f"{int(diff/3600)}h ago"
        else:
            return f"{int(diff/86400)}d ago"

    def display_error(self, message: str):
        """Display error message."""
        self.console.print(Panel(f"[bold red]Error:[/bold red] {message}", border_style="red"))

    def display_success(self, message: str):
        """Display success message."""
        self.console.print(Panel(f"[bold green]Success:[/bold green] {message}", border_style="green"))

    def display_info(self, message: str):
        """Display info message."""
        self.console.print(Panel(f"[bold blue]Info:[/bold blue] {message}", border_style="blue"))
