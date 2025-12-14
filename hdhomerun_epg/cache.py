import sqlite3
import gzip
import json
import logging
import time
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, db_path: str = "epg_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database and table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS epg_chunks (
                        start_time INTEGER PRIMARY KEY,
                        end_time INTEGER,
                        data BLOB,
                        fetched_at INTEGER
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_end_time ON epg_chunks (end_time)"
                )
        except Exception as e:
            logger.error(f"🚨 Failed to initialize cache DB: {e}")

    def get_chunk(
        self, start_time: int, ttl_seconds: int = 86400
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve a chunk if it exists and is fresh.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data, fetched_at FROM epg_chunks WHERE start_time = ?",
                    (start_time,),
                )
                row = cursor.fetchone()

                if row:
                    data_blob, fetched_at = row
                    age = int(time.time()) - fetched_at

                    if age < ttl_seconds:
                        logger.debug(
                            f"✅ Cache HIT for chunk {start_time} (Age: {age}s)"
                        )
                        decompressed = gzip.decompress(data_blob)
                        return json.loads(decompressed)
                    else:
                        logger.debug(
                            f"🍂 Cache STALE for chunk {start_time} (Age: {age}s)"
                        )
                        return None

                logger.debug(f"❌ Cache MISS for chunk {start_time}")
                return None
        except Exception as e:
            logger.error(f"🚨 Cache read error: {e}")
            return None

    def save_chunk(self, start_time: int, end_time: int, data: List[Dict[str, Any]]):
        """
        Save a chunk to the cache.
        """
        try:
            json_str = json.dumps(data)
            compressed = gzip.compress(json_str.encode("utf-8"))
            fetched_at = int(time.time())

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO epg_chunks (start_time, end_time, data, fetched_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (start_time, end_time, compressed, fetched_at),
                )
            logger.debug(f"💾 Cached chunk {start_time} to {end_time}")
        except Exception as e:
            logger.error(f"🚨 Cache write error: {e}")

    def clear_cache(self):
        """Clear all cached data."""
        try:
            # internal connection to allow VACUUM (cannot run in transaction)
            with sqlite3.connect(self.db_path, isolation_level=None) as conn:
                conn.execute("DELETE FROM epg_chunks")
                conn.execute("VACUUM")
            logger.info("🗑️ Cache cleared successfully")
        except Exception as e:
            logger.error(f"🚨 Error clearing cache: {e}")
            raise

    def get_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all cached chunks.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT start_time, end_time, length(data), fetched_at FROM epg_chunks ORDER BY start_time ASC"
                )
                chunks = []
                for row in cursor.fetchall():
                    chunks.append(
                        {
                            "start_time": row[0],
                            "end_time": row[1],
                            "size_bytes": row[2],
                            "fetched_at": row[3],
                        }
                    )
                return chunks
        except Exception as e:
            logger.error(f"🚨 Error getting cache status: {e}")
            return []
