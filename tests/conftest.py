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


@pytest.fixture(autouse=True)
def forget_guide_end():
    """The end of the guide is remembered per process; keep tests independent."""
    from hdhomerun_epg.client import HDHomeRunClient

    HDHomeRunClient._guide_end = None
    yield
    HDHomeRunClient._guide_end = None
