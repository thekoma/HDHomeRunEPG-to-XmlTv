import pytest
import time
import gzip
import json
import sqlite3
from hdhomerun_epg.cache import CacheManager

def test_cache_init(temp_db_path):
    cm = CacheManager(temp_db_path)
    assert os.path.exists(temp_db_path)
    
def test_save_and_get_chunk(temp_db_path):
    cm = CacheManager(temp_db_path)
    start_time = 1000
    end_time = 2000
    data = [{"program": "test"}]
    
    cm.save_chunk(start_time, end_time, data)
    
    # Test internal storage
    with sqlite3.connect(temp_db_path) as conn:
        cursor = conn.execute("SELECT * FROM epg_chunks WHERE start_time=?", (start_time,))
        row = cursor.fetchone()
        assert row is not None
        
    # Test retrieval
    cached_data = cm.get_chunk(start_time, ttl_seconds=3600)
    assert cached_data == data

def test_cache_miss(temp_db_path):
    cm = CacheManager(temp_db_path)
    data = cm.get_chunk(9999)
    assert data is None

def test_cache_expiry(temp_db_path):
    cm = CacheManager(temp_db_path)
    start_time = 5000
    cm.save_chunk(start_time, 6000, [{"p": "old"}])
    
    # Manually backdate the fetched_at
    with sqlite3.connect(temp_db_path) as conn:
        # Set fetched_at to 2 hours ago
        past_time = int(time.time()) - 7200
        conn.execute("UPDATE epg_chunks SET fetched_at=? WHERE start_time=?", (past_time, start_time))
        
    # TTL is 1 hour, so should be stale (None)
    data = cm.get_chunk(start_time, ttl_seconds=3600)
    assert data is None

def test_clear_cache(temp_db_path):
    cm = CacheManager(temp_db_path)
    cm.save_chunk(1, 2, [{"a":1}])
    cm.clear_cache()
    
    with sqlite3.connect(temp_db_path) as conn:
        cursor = conn.execute("SELECT count(*) FROM epg_chunks")
        assert cursor.fetchone()[0] == 0

import os
