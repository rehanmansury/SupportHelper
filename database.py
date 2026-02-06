import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clip_snippet_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = 'clip_snippet_manager.db'):
        self.db_path = db_path
        self._init_db()
        
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create snippets table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Create clipboard_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS clipboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                content_data BLOB,
                content_text TEXT,
                preview TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Create world_clocks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS world_clocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                timezone TEXT NOT NULL
            )''')

            # Schema migration: add use_dst column if not exists
            cursor.execute("PRAGMA table_info(world_clocks)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'use_dst' not in cols:
                cursor.execute('ALTER TABLE world_clocks ADD COLUMN use_dst INTEGER NOT NULL DEFAULT 1')

            # Create settings table for app-wide preferences
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )''')
            
            # Create custom_urls table for World Clock Integrations
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                integration_type TEXT NOT NULL DEFAULT 'email',
                app_path TEXT,
                parameters TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Create wc_parameters table for World Clock parameters
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS wc_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                param_name TEXT NOT NULL UNIQUE,
                param_display TEXT NOT NULL,
                param_description TEXT,
                param_sample TEXT,
                param_category TEXT DEFAULT 'meeting'
            )''')
            
            # Insert default World Clock parameters
            cursor.execute('''
            INSERT OR IGNORE INTO wc_parameters (param_name, param_display, param_description, param_sample, param_category) VALUES
            ('%wc_city_name%', 'City Name', 'Name of the selected city', 'Houston', 'basic'),
            ('%wc_local_time%', 'Local Time', 'Your local time for the meeting', '2026-01-30 14:00', 'time'),
            ('%wc_target_time%', 'Target Time', 'Target city time for the meeting', '2026-01-30 02:30', 'time'),
            ('%wc_duration%', 'Duration', 'Meeting duration in minutes', '60', 'meeting'),
            ('%wc_meeting_url%', 'Meeting URL', 'Generated meeting URL', 'https://teams.microsoft.com/...', 'meeting'),
            ('%wc_timezone%', 'Timezone', 'Target city timezone', 'America/Chicago', 'basic'),
            ('%wc_local_timezone%', 'Local Timezone', 'Your local timezone', 'Asia/Kolkata', 'basic'),
            ('%wc_date%', 'Date', 'Meeting date', '2026-01-30', 'basic'),
            ('%wc_end_time%', 'End Time', 'Meeting end time (local)', '2026-01-30 15:00', 'time'),
            ('%wc_target_end_time%', 'Target End Time', 'Meeting end time (target)', '2026-01-30 03:30', 'time')
            ''')
            
            # Create indexes
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_snippets_category 
            ON snippets(category)''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_snippets_title 
            ON snippets(title)''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_snippets_content 
            ON snippets(content)''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_clipboard_created 
            ON clipboard_history(created_at)''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_clipboard_content_type 
            ON clipboard_history(content_type)''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_clipboard_content_text 
            ON clipboard_history(content_text)''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_clipboard_preview 
            ON clipboard_history(preview)''')
            
            # Create full-text search virtual tables for faster search
            cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS snippets_fts USING fts5(title, content, category, content='snippets', content_rowid='id')''')
            
            cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS clipboard_fts USING fts5(content_text, preview, content='clipboard_history', content_rowid='id')''')
            
            # Create triggers to keep FTS tables in sync
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS snippets_fts_insert AFTER INSERT ON snippets BEGIN
                INSERT INTO snippets_fts(rowid, title, content, category) VALUES (new.id, new.title, new.content, new.category);
            END''')
            
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS snippets_fts_delete AFTER DELETE ON snippets BEGIN
                INSERT INTO snippets_fts(snippets_fts, rowid, title, content, category) VALUES('delete', old.id, old.title, old.content, old.category);
            END''')
            
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS snippets_fts_update AFTER UPDATE ON snippets BEGIN
                INSERT INTO snippets_fts(snippets_fts, rowid, title, content, category) VALUES('delete', old.id, old.title, old.content, old.category);
                INSERT INTO snippets_fts(rowid, title, content, category) VALUES (new.id, new.title, new.content, new.category);
            END''')
            
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS clipboard_fts_insert AFTER INSERT ON clipboard_history BEGIN
                INSERT INTO clipboard_fts(rowid, content_text, preview) VALUES (new.id, new.content_text, new.preview);
            END''')
            
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS clipboard_fts_delete AFTER DELETE ON clipboard_history BEGIN
                INSERT INTO clipboard_fts(clipboard_fts, rowid, content_text, preview) VALUES('delete', old.id, old.content_text, old.preview);
            END''')
            
            conn.commit()
            
    # Snippet operations
    def add_snippet(self, title: str, content: str, category: str = '') -> int:
        """Add a new snippet to the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO snippets (title, content, category, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (title, content, category))
            conn.commit()
            return cursor.lastrowid
            
    def update_snippet(self, snippet_id: int, title: str, content: str, category: str = '') -> bool:
        """Update an existing snippet"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE snippets 
                SET title = ?, content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (title, content, category, snippet_id))
            conn.commit()
            return cursor.rowcount > 0
            
    def delete_snippet(self, snippet_id: int) -> bool:
        """Delete a snippet by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM snippets WHERE id = ?', (snippet_id,))
            conn.commit()
            return cursor.rowcount > 0
            
    def get_snippet(self, snippet_id: int) -> Optional[Dict[str, Any]]:
        """Get a single snippet by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM snippets WHERE id = ?', (snippet_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def get_all_snippets(self, category: str = None) -> List[Dict[str, Any]]:
        """Get all snippets, optionally filtered by category"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category is not None and category != "":
                cursor.execute('SELECT * FROM snippets WHERE category = ? ORDER BY title', (category,))
            elif category == "":
                # Filter for snippets with empty/NULL category
                cursor.execute('SELECT * FROM snippets WHERE (category IS NULL OR category = "") ORDER BY title')
            else:
                cursor.execute('SELECT * FROM snippets ORDER BY title')
            return [dict(row) for row in cursor.fetchall()]
            
    def get_snippet_categories(self) -> List[str]:
        """Get all unique snippet categories"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM snippets WHERE category IS NOT NULL AND category != ""')
            return [row[0] for row in cursor.fetchall()]

    def rename_snippet_category(self, old_category: str, new_category: str) -> int:
        """Rename a category across all snippets. Returns number of affected rows."""
        if not old_category or new_category is None:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE snippets SET category = ?, updated_at = CURRENT_TIMESTAMP WHERE category = ?',
                (new_category, old_category)
            )
            conn.commit()
            return cursor.rowcount

    def delete_snippet_category(self, category: str) -> int:
        """Clear the category on all snippets that currently use it. Returns affected count."""
        if not category:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE snippets SET category = "", updated_at = CURRENT_TIMESTAMP WHERE category = ?',
                (category,)
            )
            conn.commit()
            return cursor.rowcount
            
    # Clipboard history operations
    def add_clipboard_item(self, content_type: str, content_data: bytes = None, 
                          content_text: str = None, preview: str = None) -> int:
        """Add a new item to clipboard history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clipboard_history (content_type, content_data, content_text, preview)
                VALUES (?, ?, ?, ?)
            ''', (content_type, content_data, content_text, preview))
            conn.commit()
            return cursor.lastrowid
            
    def get_clipboard_items(self, start_date=None, end_date=None, content_type=None, search_term=None, limit=None, search_all_dates=False) -> List[Dict]:
        """Retrieve clipboard items with optional filtering"""
        import time
        start_time = time.time()
        
        # Add default limit to prevent loading too many items at once
        if limit is None and not search_term and not search_all_dates:
            # For non-search queries, limit to 500 most recent items for better performance
            limit = 500
        
        query = '''
        SELECT 
            id, 
            content_type, 
            content_data, 
            content_text, 
            preview, 
            strftime('%Y-%m-%d %H:%M:%S', datetime(created_at, 'localtime')) as created_at
        FROM clipboard_history 
        WHERE 1=1
        '''
        params = []
        
        # Default to last 30 days unless searching all dates or specific date range
        if not start_date and not end_date and not search_all_dates:
            from datetime import datetime, timedelta
            default_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            query += " AND date(datetime(created_at, 'localtime')) >= date(?)"
            params.append(default_start)
        
        # Date filtering in local time
        if start_date and end_date:
            # Inclusive range on local dates
            query += " AND date(datetime(created_at, 'localtime')) BETWEEN date(?) AND date(?)"
            params.extend([start_date, end_date])
        elif start_date:
            # Exact match on selected local date
            query += " AND date(datetime(created_at, 'localtime')) = date(?)"
            params.append(start_date)
        
        # Content type filtering
        if content_type and content_type != 'all':
            query += ' AND content_type = ?'
            params.append(content_type.lower())
        elif search_term:
            # Only exclude images when searching (not when filtering by type)
            query += ' AND content_type != ?'
            params.append('image')
        
        if search_term:
            # Use LIKE for wildcard text search (excluding images already handled above)
            search_term = f'%{search_term}%'
            query += ' AND (content_text LIKE ? OR preview LIKE ?)'
            params.extend([search_term, search_term])
        
        query += ' ORDER BY created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
        end_time = time.time()
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"PERF: get_clipboard_items(date_range={start_date}-{end_date}, type={content_type}, search={bool(search_term)}, limit={limit}, search_all_dates={search_all_dates}) - {len(results)} results in {query_time:.2f}ms")
        
        return results
            
    def get_clipboard_dates(self) -> List[str]:
        """Get all unique dates with clipboard history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT date(datetime(created_at, 'localtime')) as clip_date 
                FROM clipboard_history 
                ORDER BY clip_date DESC
            ''')
            return [row[0] for row in cursor.fetchall()]
            
    def optimize_database(self):
        """Optimize database performance"""
        import time
        start_time = time.time()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Analyze tables to update query planner statistics
            cursor.execute('ANALYZE')
            
            # Rebuild indexes
            cursor.execute('REINDEX')
            
            # Optimize database file
            cursor.execute('VACUUM')
            
            conn.commit()
            
        end_time = time.time()
        optimization_time = (end_time - start_time) * 1000
        print(f"PERF: Database optimization completed in {optimization_time:.2f}ms")
            
    def cleanup_old_items(self, days_to_keep: int = 30) -> int:
        """Remove clipboard items older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        # First, delete in a transaction and commit
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM clipboard_history WHERE date(created_at) < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()

        # Then, VACUUM in a separate autocommit connection (VACUUM cannot run inside a transaction)
        if deleted_count > 0:
            try:
                conn2 = sqlite3.connect(self.db_path)
                # Ensure autocommit mode for VACUUM
                conn2.isolation_level = None
                conn2.execute('VACUUM')
                conn2.close()
            except Exception as e:
                logger.warning(f"VACUUM failed: {e}")
        
        return deleted_count
            
    def search_snippets(self, search_term: str, category: str = None) -> List[Dict[str, Any]]:
        """Search snippets by title or content, optionally filtered by category"""
        import time
        start_time = time.time()
        
        search_term = f'%{search_term}%'
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category is not None and category != "":
                cursor.execute('''
                    SELECT * FROM snippets 
                    WHERE (title LIKE ? OR content LIKE ?) AND category = ?
                    ORDER BY title
                ''', (search_term, search_term, category))
            elif category == "":
                # Search in snippets with empty/NULL category
                cursor.execute('''
                    SELECT * FROM snippets 
                    WHERE (title LIKE ? OR content LIKE ?) AND (category IS NULL OR category = "")
                    ORDER BY title
                ''', (search_term, search_term))
            else:
                # Search all snippets
                cursor.execute('''
                    SELECT * FROM snippets 
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY title
                ''', (search_term, search_term))
            
            results = [dict(row) for row in cursor.fetchall()]
            
        end_time = time.time()
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"PERF: search_snippets(category='{category}') - {len(results)} results in {query_time:.2f}ms")
        
        return results
            
    # Settings operations
    def set_setting(self, key: str, value: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
            conn.commit()
            
    def get_setting(self, key: str, default: str = None) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else default
            
    def get_settings(self) -> Dict[str, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM settings')
            return {row[0]: row[1] for row in cursor.fetchall()}
            
    # World clock operations
    def get_world_clocks(self) -> List[Dict[str, Any]]:
        """Retrieve all saved world clock entries"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, city, timezone, COALESCE(use_dst, 1) as use_dst FROM world_clocks ORDER BY city')
            return [dict(row) for row in cursor.fetchall()]
            
    def add_world_clock(self, city: str, timezone: str, use_dst: int = 1) -> int:
        """Add a new world clock entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(world_clocks)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'use_dst' in cols:
                cursor.execute('INSERT INTO world_clocks (city, timezone, use_dst) VALUES (?, ?, ?)', (city, timezone, use_dst))
            else:
                cursor.execute('INSERT INTO world_clocks (city, timezone) VALUES (?, ?)', (city, timezone))
            conn.commit()
            return cursor.lastrowid
            
    def delete_world_clock(self, clock_id: int) -> bool:
        """Delete a world clock entry by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM world_clocks WHERE id = ?', (clock_id,))
            conn.commit()
            return cursor.rowcount > 0
            
    def update_world_clock_dst(self, clock_id: int, use_dst: int) -> bool:
        """Update the per-clock DST usage flag"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE world_clocks SET use_dst = ? WHERE id = ?', (use_dst, clock_id))
            conn.commit()
            return cursor.rowcount > 0
            
    def save_custom_meeting_url(self, url: str) -> None:
        """Save custom meeting URL setting (deprecated - use save_custom_url)"""
        self.save_custom_url("Default", url)
            
    def get_custom_meeting_url(self) -> str:
        """Get custom meeting URL setting (deprecated - use get_custom_urls)"""
        urls = self.get_custom_urls()
        return urls.get("Default", "") if urls else ""
            
    def save_email_app_path(self, app_name: str, path: str) -> None:
        """Save email application path"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', 
                          (f'email_app_{app_name}', path))
            conn.commit()
            
    def get_email_app_path(self, app_name: str) -> str:
        """Get email application path"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (f'email_app_{app_name}',))
            result = cursor.fetchone()
            return result['value'] if result else ""
    
    # ========== New World Clock Integration Methods ==========
    
    def save_custom_url(self, name: str, url: str, integration_type: str = 'email', app_path: str = "", parameters: str = "") -> None:
        """Save a custom URL integration"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO custom_urls (name, url, integration_type, app_path, parameters, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (name, url, integration_type, app_path, parameters))
            conn.commit()
            
    def get_custom_urls(self) -> Dict[str, Dict]:
        """Get all custom URLs as a dictionary of name->{url, integration_type, app_path, parameters}"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, url, integration_type, app_path, parameters FROM custom_urls ORDER BY name')
            results = cursor.fetchall()
            return {row['name']: {
                'url': row['url'],
                'integration_type': row['integration_type'],
                'app_path': row['app_path'],
                'parameters': row['parameters']
            } for row in results}
            
    def delete_custom_url(self, name: str) -> bool:
        """Delete a custom URL by name"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM custom_urls WHERE name = ?', (name,))
            conn.commit()
            return cursor.rowcount > 0
            
    def get_wc_parameters(self) -> List[Dict]:
        """Get all World Clock parameters"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT param_name, param_display, param_description, param_sample, param_category FROM wc_parameters ORDER BY param_category, param_display')
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
    def add_wc_parameter(self, param_name: str, param_display: str, param_description: str = "", param_sample: str = "", param_category: str = "custom") -> None:
        """Add a new World Clock parameter"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO wc_parameters (param_name, param_display, param_description, param_sample, param_category)
            VALUES (?, ?, ?, ?, ?)
            ''', (param_name, param_display, param_description, param_sample, param_category))
            conn.commit()
            
    def delete_wc_parameter(self, param_name: str) -> bool:
        """Delete a World Clock parameter by name"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM wc_parameters WHERE param_name = ?', (param_name,))
            conn.commit()
            return cursor.rowcount > 0
