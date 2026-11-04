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


# A trimmed copy of SiliconDust's XMLTV feed: one station on two channel numbers.
OFFICIAL_FEED = b"""<?xml version="1.0" encoding="utf-8"?>
<tv source-info-name="HDHomeRun">
  <channel id="EU1.hdhomerun.com"><display-name>RAI3RLO</display-name><lcn>3</lcn></channel>
  <channel id="EU1.hdhomerun.com"><display-name>RAI3RPI</display-name><lcn>802</lcn></channel>
  <programme start="20261104172300 +0000" stop="20261104181500 +0000" channel="EU1.hdhomerun.com">
    <title>1939-1945</title>
    <sub-title>L'Italia in guerra</sub-title>
    <desc lang="it">Il 10 giugno 1940.</desc>
    <category>Series</category>
    <category>Documentary</category>
    <language>it</language>
    <series-id system="cseries">C12126221ITNGVU</series-id>
    <episode-num system="dd_progid">EP02267119.0018</episode-num>
    <episode-num system="onscreen">S01E03</episode-num>
    <star-rating><value>2.0/4.0</value></star-rating>
  </programme>
  <programme start="20261104172300 +0000" stop="20261104181500 +0000" channel="EU9.hdhomerun.com">
    <title>A station without a channel element</title>
  </programme>
</tv>"""
OFFICIAL_START = 1793812980  # 2026-11-04 17:23 UTC
