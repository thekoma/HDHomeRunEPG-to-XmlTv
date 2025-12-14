import pytest
from hdhomerun_epg.config import settings


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "cache_enabled", True)
    monkeypatch.setattr(
        settings, "cache_db_path", ":memory:"
    )  # Use in-memory DB for tests
    return settings


@pytest.fixture
def temp_db_path(tmp_path):
    d = tmp_path / "test_epg_cache.db"
    return str(d)
