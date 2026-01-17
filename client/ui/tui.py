"""Terminal User Interface using Rich - Fixed with proper command input."""
import asyncio
import logging
import sys
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from .screens import Screens
from .handlers import UIHandlers

logger = logging.getLogger(__name__)


class TUI:
    """Terminal User Interface manager with command input."""

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
            await self._show_status()
            self._show_help()

            # Main command loop
            await self._main_loop()

        except Exception as e:
            logger.error(f"Error in TUI: {e}", exc_info=True)
            self.console.print(f"[bold red]TUI error: {e}[/bold red]")
        finally:
            self.running = False

    async def _main_loop(self):
        """Main TUI command loop with keyboard input."""
        self.console.print("\n[bold cyan]Enter command (type 'help' for commands):[/bold cyan]")
        
        while self.running:
            try:
                # Use asyncio to read input without blocking
                loop = asyncio.get_event_loop()
                
                # Print prompt
                self.console.print("[green]> [/green]", end="")
                
                # Read input asynchronously
                cmd = await loop.run_in_executor(None, sys.stdin.readline)
                cmd = cmd.strip()
                
                if cmd:
                    await self._handle_command(cmd)
                    
            except KeyboardInterrupt:
                logger.info("TUI interrupted by user")
                self.running = False
                break
            except EOFError:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in TUI main loop: {e}", exc_info=True)
                self.console.print(f"[red]Error: {e}[/red]")

    async def _handle_command(self, cmd: str):
        """Handle user command."""
        parts = cmd.split(maxsplit=2)
        command = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        try:
            if command == "status":
                await self._show_status()
            elif command == "pair":
                if args:
                    # Pair with specific device ID
                    await self._pair_with_device(args[0])
                else:
                    # Show pairing info
                    await self._start_pairing()
            elif command == "devices":
                await self._show_devices()
            elif command == "connect":
                if args:
                    await self._connect_device(args[0])
                else:
                    self.console.print("[red]Usage: connect <device_id>[/red]")
            elif command == "disconnect":
                if args:
                    await self._disconnect_device(args[0])
                else:
                    self.console.print("[red]Usage: disconnect <device_id>[/red]")
            elif command == "send":
                if len(args) >= 2:
                    await self._send_snippet(args[0], args[1])
                else:
                    self.console.print("[red]Usage: send <device_id> \"<text>\"[/red]")
            elif command == "history":
                await self._show_history()
            elif command == "logs":
                await self._show_logs()
            elif command in ["exit", "quit", "q"]:
                self.console.print("[yellow]Shutting down...[/yellow]")
                self.running = False
            elif command in ["help", "?"]:
                self._show_help()
            elif command == "clear":
                self.console.clear()
            elif command == "refresh" or command == "r":
                await self._show_status()
            else:
                self.console.print(f"[red]Unknown command: {command}. Type 'help' for commands.[/red]")
        except Exception as e:
            logger.error(f"Error handling command '{cmd}': {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

    def _show_help(self):
        """Show help message."""
        help_table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
        help_table.add_column("Command", style="green")
        help_table.add_column("Description")
        
        help_table.add_row("status", "Show device info, server connection, paired devices")
        help_table.add_row("pair", "Show your device ID and pairing code")
        help_table.add_row("pair <device_id>", "Send pairing request to another device")
        help_table.add_row("devices", "List all paired devices and their status")
        help_table.add_row("connect <id>", "Connect to a paired device")
        help_table.add_row("disconnect <id>", "Disconnect from a device")
        help_table.add_row("send <id> \"text\"", "Send text snippet to a device")
        help_table.add_row("history", "Show clipboard sync history")
        help_table.add_row("logs", "Show recent log entries")
        help_table.add_row("clear", "Clear the screen")
        help_table.add_row("exit / quit / q", "Exit the application")
        
        self.console.print(help_table)

    async def _show_status(self):
        """Show current status."""
        try:
            device_id = self.app.device_id
            device_name = self.app.config.get('device_name', 'Unknown')
            server_url = self.app.config.get('server_url', 'Not set')
            connected = self.app.signaling_client.connected
            
            paired_devices = await self.app.device_registry.get_all_paired_devices()
            online_count = sum(1 for d in paired_devices if d.get('status') == 'online')
            
            # Create status panel
            status_text = Text()
            status_text.append("Device Name: ", style="bold")
            status_text.append(f"{device_name}\n")
            status_text.append("Device ID: ", style="bold")
            status_text.append(f"{device_id[:16]}...\n")
            status_text.append("Server URL: ", style="bold")
            status_text.append(f"{server_url}\n")
            status_text.append("Server Status: ", style="bold")
            status_text.append("🟢 Connected" if connected else "🔴 Disconnected", 
                             style="green" if connected else "red")
            status_text.append(f"\nPaired Devices: ", style="bold")
            status_text.append(f"{len(paired_devices)} ({online_count} online)")
            
            panel = Panel(status_text, title="[bold blue]Status[/bold blue]", border_style="blue")
            self.console.print(panel)
            
        except Exception as e:
            logger.error(f"Error showing status: {e}", exc_info=True)
            self.console.print(f"[red]Error getting status: {e}[/red]")

    async def _show_devices(self):
        """Show paired devices."""
        try:
            devices = await self.app.device_registry.get_all_paired_devices()
            
            if not devices:
                self.console.print("[yellow]No paired devices. Use 'pair' to add a device.[/yellow]")
                return
            
            table = Table(title="Paired Devices", show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Device ID", style="dim")
            table.add_column("Type")
            table.add_column("Status")
            table.add_column("Last Seen")
            
            for device in devices:
                status = device.get('status', 'unknown')
                status_icon = "🟢" if status == 'online' else "🔴"
                
                last_seen = device.get('last_seen', 0)
                if last_seen:
                    last_seen_str = datetime.fromtimestamp(last_seen).strftime("%Y-%m-%d %H:%M")
                else:
                    last_seen_str = "Never"
                
                table.add_row(
                    device.get('device_name', 'Unknown'),
                    device.get('device_id', '')[:16] + "...",
                    device.get('device_type', 'Unknown'),
                    f"{status_icon} {status}",
                    last_seen_str
                )
            
            self.console.print(table)
            
        except Exception as e:
            logger.error(f"Error showing devices: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

    async def _start_pairing(self):
        """Start pairing flow."""
        try:
            self.console.print("[cyan]Generating pairing code...[/cyan]")
            
            # Generate pairing payload
            qr_payload = self.app.pairing_manager.generate_pairing_qr(
                self.app.device_id,
                self.app.config.get('device_name', 'My Device'),
                self.app.config.get('device_type', 'Linux'),
                self.app.config.get('server_url', 'http://localhost:5000'),
                self.app.public_key
            )
            
            # Display QR code as ASCII
            qr_ascii = self.app.pairing_manager.get_qr_as_ascii(qr_payload)
            self.console.print(qr_ascii)
            
            # Also show the pairing code for manual entry
            self.console.print(f"\n[bold]Pairing Code:[/bold] {self.app.device_id[:8]}")
            self.console.print(f"[bold]Device ID:[/bold] {self.app.device_id}")
            self.console.print("\n[yellow]On the other device, run:[/yellow]")
            self.console.print(f"[cyan]  pair {self.app.device_id}[/cyan]")
            self.console.print("\n[yellow]Or scan the QR code above.[/yellow]")
            
        except Exception as e:
            logger.error(f"Error starting pairing: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

    async def _pair_with_device(self, device_id: str):
        """Pair with a specific device by ID."""
        try:
            self.console.print(f"[cyan]Pairing with device {device_id[:8]}...[/cyan]")
            
            # Send pairing request via signaling server
            await self.app.signaling_client.send_pairing_request(
                device_id,
                self.app.device_id,
                self.app.config.get('device_name', 'My Device'),
                self.app.config.get('device_type', 'Linux')
            )
            
            self.console.print(f"[green]✓ Pairing request sent to {device_id[:8]}...[/green]")
            self.console.print("[yellow]Waiting for the other device to accept...[/yellow]")
            
        except Exception as e:
            logger.error(f"Error pairing with device: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")


    async def _connect_device(self, device_id: str):
        """Connect to a device."""
        try:
            # Find full device ID if partial
            devices = await self.app.device_registry.get_all_paired_devices()
            full_id = None
            for d in devices:
                if d['device_id'].startswith(device_id):
                    full_id = d['device_id']
                    break
            
            if not full_id:
                self.console.print(f"[red]Device not found: {device_id}[/red]")
                return
            
            self.console.print(f"[cyan]Connecting to {full_id[:16]}...[/cyan]")
            await self.app.webrtc_manager.create_offer(full_id, self.app.signaling_client)
            self.console.print(f"[green]Connection initiated. WebRTC offer sent.[/green]")
            
        except Exception as e:
            logger.error(f"Error connecting to device: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

    async def _disconnect_device(self, device_id: str):
        """Disconnect from a device."""
        try:
            # Find full device ID if partial
            devices = await self.app.device_registry.get_all_paired_devices()
            full_id = None
            for d in devices:
                if d['device_id'].startswith(device_id):
                    full_id = d['device_id']
                    break
            
            if not full_id:
                self.console.print(f"[red]Device not found: {device_id}[/red]")
                return
            
            self.console.print(f"[cyan]Disconnecting from {full_id[:16]}...[/cyan]")
            await self.app.webrtc_manager.close_peer_connection(full_id)
            self.console.print(f"[green]Disconnected.[/green]")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

    async def _send_snippet(self, device_id: str, text: str):
        """Send text snippet to a device."""
        try:
            # Remove quotes if present
            text = text.strip('"\'')
            
            # Find full device ID if partial
            devices = await self.app.device_registry.get_all_paired_devices()
            full_id = None
            for d in devices:
                if d['device_id'].startswith(device_id):
                    full_id = d['device_id']
                    break
            
            if not full_id:
                self.console.print(f"[red]Device not found: {device_id}[/red]")
                return
            
            self.console.print(f"[cyan]Sending to {full_id[:16]}...[/cyan]")
            
            success = await self.app.sync_engine.sync_to_peer(
                full_id, text, self.app.device_id, self.app.config.get('device_name')
            )
            
            if success:
                self.console.print(f"[green]✓ Sent: \"{text[:50]}{'...' if len(text) > 50 else ''}\"[/green]")
            else:
                self.console.print(f"[red]✗ Failed to send. Device may be offline or not connected.[/red]")
                
        except Exception as e:
            logger.error(f"Error sending snippet: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

    async def _show_history(self):
        """Show clipboard history."""
        try:
            history = await self.app.clipboard_history.get_history(limit=20)
            
            if not history:
                self.console.print("[yellow]No clipboard history yet.[/yellow]")
                return
            
            table = Table(title="Clipboard History (Last 20)", show_header=True, header_style="bold green")
            table.add_column("#", style="dim", width=4)
            table.add_column("Content", max_width=60)
            table.add_column("Source", style="cyan")
            table.add_column("Time")
            
            for i, item in enumerate(history, 1):
                content = item.get('content', '')[:60]
                if len(item.get('content', '')) > 60:
                    content += "..."
                
                timestamp = item.get('timestamp', 0)
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S") if timestamp else "?"
                
                source = item.get('source_device_id', '')[:8] + "..."
                
                table.add_row(str(i), content, source, time_str)
            
            self.console.print(table)
            
        except Exception as e:
            logger.error(f"Error showing history: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

    async def _show_logs(self):
        """Show recent log entries."""
        try:
            log_path = os.path.expanduser("~/.clipboard-sync/client.log")
            
            if not os.path.exists(log_path):
                self.console.print("[yellow]No log file found.[/yellow]")
                return
            
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            # Show last 30 lines
            recent = lines[-30:] if len(lines) > 30 else lines
            
            self.console.print("[bold]Recent Logs:[/bold]")
            for line in recent:
                line = line.strip()
                if "ERROR" in line:
                    self.console.print(f"[red]{line}[/red]")
                elif "WARNING" in line:
                    self.console.print(f"[yellow]{line}[/yellow]")
                else:
                    self.console.print(f"[dim]{line}[/dim]")
                    
        except Exception as e:
            logger.error(f"Error showing logs: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")

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
        await self._show_status()

    async def stop(self):
        """Stop the TUI."""
        self.running = False
        logger.info("TUI stopped")
