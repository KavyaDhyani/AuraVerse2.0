"""Local SQLite database for persistent storage."""
import aiosqlite
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Database:
    """Manages local SQLite database."""

    def __init__(self, db_path: str = None):
        """
        Initialize database.

        Args:
            db_path: Path to database file
        """
        if db_path is None:
            home = Path.home()
            config_dir = home / '.clipboard-sync'
            config_dir.mkdir(exist_ok=True)
            db_path = str(config_dir / 'clipboard_sync.db')

        self.db_path = db_path
        logger.info(f"Database initialized at: {db_path}")

    async def initialize_database(self):
        """Create database tables if they don't exist."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Paired devices table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS paired_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        public_key TEXT,
                        date_paired REAL NOT NULL,
                        last_seen REAL NOT NULL,
                        sync_enabled INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'offline'
                    )
                ''')

                # Clipboard history table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS clipboard_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        source_device_id TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        content_type TEXT DEFAULT 'text'
                    )
                ''')

                # Offline queue table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS offline_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        peer_device_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        retry_count INTEGER DEFAULT 0
                    )
                ''')

                # Sync preferences table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS sync_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                ''')

                await db.commit()
                logger.info("Database tables initialized")

        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    async def save_paired_device(self, device_info: dict):
        """Save or update paired device."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO paired_devices
                    (device_id, device_name, device_type, public_key, date_paired, last_seen, sync_enabled, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_info['device_id'],
                    device_info['device_name'],
                    device_info['device_type'],
                    device_info.get('public_key', ''),
                    device_info['date_paired'],
                    device_info['last_seen'],
                    1 if device_info.get('sync_enabled', True) else 0,
                    device_info.get('status', 'offline')
                ))
                await db.commit()
                logger.debug(f"Saved paired device: {device_info['device_id']}")
        except Exception as e:
            logger.error(f"Error saving paired device: {e}", exc_info=True)
            raise

    async def load_paired_devices(self) -> List[dict]:
        """Load all paired devices."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('SELECT * FROM paired_devices') as cursor:
                    rows = await cursor.fetchall()
                    devices = []
                    for row in rows:
                        devices.append({
                            'device_id': row['device_id'],
                            'device_name': row['device_name'],
                            'device_type': row['device_type'],
                            'public_key': row['public_key'],
                            'date_paired': row['date_paired'],
                            'last_seen': row['last_seen'],
                            'sync_enabled': bool(row['sync_enabled']),
                            'status': row['status']
                        })
                    return devices
        except Exception as e:
            logger.error(f"Error loading paired devices: {e}", exc_info=True)
            return []

    async def delete_paired_device(self, device_id: str):
        """Delete paired device."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM paired_devices WHERE device_id = ?', (device_id,))
                await db.commit()
                logger.debug(f"Deleted paired device: {device_id}")
        except Exception as e:
            logger.error(f"Error deleting paired device: {e}", exc_info=True)
            raise

    async def update_device_status(self, device_id: str, status: str):
        """Update device status."""
        try:
            import time
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE paired_devices SET status = ?, last_seen = ? WHERE device_id = ?
                ''', (status, time.time(), device_id))
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating device status: {e}", exc_info=True)

    async def update_device_sync_enabled(self, device_id: str, enabled: bool):
        """Update device sync enabled status."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE paired_devices SET sync_enabled = ? WHERE device_id = ?
                ''', (1 if enabled else 0, device_id))
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating sync enabled: {e}", exc_info=True)

    async def save_clipboard_item(self, content: str, source_device_id: str, timestamp: float):
        """Save clipboard item to history."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO clipboard_history (content, source_device_id, timestamp, content_type)
                    VALUES (?, ?, ?, ?)
                ''', (content, source_device_id, timestamp, 'text'))
                await db.commit()
                logger.debug(f"Saved clipboard item from {source_device_id}")
        except Exception as e:
            logger.error(f"Error saving clipboard item: {e}", exc_info=True)

    async def load_clipboard_history(self, limit: int = 50) -> List[dict]:
        """Load clipboard history."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('''
                    SELECT * FROM clipboard_history ORDER BY timestamp DESC LIMIT ?
                ''', (limit,)) as cursor:
                    rows = await cursor.fetchall()
                    history = []
                    for row in rows:
                        history.append({
                            'id': row['id'],
                            'content': row['content'],
                            'source_device_id': row['source_device_id'],
                            'timestamp': row['timestamp'],
                            'content_type': row['content_type']
                        })
                    return history
        except Exception as e:
            logger.error(f"Error loading clipboard history: {e}", exc_info=True)
            return []

    async def clear_clipboard_history(self):
        """Clear all clipboard history."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM clipboard_history')
                await db.commit()
                logger.info("Cleared clipboard history")
        except Exception as e:
            logger.error(f"Error clearing clipboard history: {e}", exc_info=True)

    async def save_offline_queue_item(self, peer_device_id: str, content: str, timestamp: float):
        """Save item to offline queue."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO offline_queue (peer_device_id, content, timestamp, retry_count)
                    VALUES (?, ?, ?, ?)
                ''', (peer_device_id, content, timestamp, 0))
                await db.commit()
                logger.debug(f"Saved offline queue item for {peer_device_id}")
        except Exception as e:
            logger.error(f"Error saving offline queue item: {e}", exc_info=True)

    async def load_offline_queue(self, peer_device_id: str) -> List[dict]:
        """Load offline queue for a peer."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute('''
                    SELECT * FROM offline_queue WHERE peer_device_id = ? ORDER BY timestamp ASC
                ''', (peer_device_id,)) as cursor:
                    rows = await cursor.fetchall()
                    queue = []
                    for row in rows:
                        queue.append({
                            'id': row['id'],
                            'peer_device_id': row['peer_device_id'],
                            'content': row['content'],
                            'timestamp': row['timestamp'],
                            'retry_count': row['retry_count']
                        })
                    return queue
        except Exception as e:
            logger.error(f"Error loading offline queue: {e}", exc_info=True)
            return []

    async def clear_offline_queue(self, peer_device_id: str):
        """Clear offline queue for a peer."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM offline_queue WHERE peer_device_id = ?', (peer_device_id,))
                await db.commit()
                logger.debug(f"Cleared offline queue for {peer_device_id}")
        except Exception as e:
            logger.error(f"Error clearing offline queue: {e}", exc_info=True)

    async def clear_all_data(self):
        """Clear all data (for uninstall)."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM paired_devices')
                await db.execute('DELETE FROM clipboard_history')
                await db.execute('DELETE FROM offline_queue')
                await db.execute('DELETE FROM sync_preferences')
                await db.commit()
                logger.info("Cleared all data")
        except Exception as e:
            logger.error(f"Error clearing all data: {e}", exc_info=True)
