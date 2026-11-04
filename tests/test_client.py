import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from hdhomerun_epg.cache import CacheManager
from hdhomerun_epg.client import HDHomeRunClient
from hdhomerun_epg.official import parse_details
from tests.conftest import OFFICIAL_FEED, OFFICIAL_START


@pytest.fixture
def mock_discovery_response():
    return {"DeviceAuth": "TEST_AUTH_TOKEN"}


@pytest.fixture
def mock_lineup_response():
    return [{"GuideNumber": "10.1", "GuideName": "Test Channel"}]


def test_discovery(mock_discovery_response):
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_discovery_response
        mock_get.return_value.raise_for_status = MagicMock()

        client = HDHomeRunClient("1.2.3.4")
        auth = client.discover_device_auth()

        assert auth == "TEST_AUTH_TOKEN"
        mock_get.assert_called_with("http://1.2.3.4/discover.json", timeout=10)


def test_fetch_channels(mock_lineup_response):
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_lineup_response

        client = HDHomeRunClient("1.2.3.4")
        client.device_auth = "EXISTING_AUTH"  # Bypass discovery
        channels = client.fetch_channels()

        assert len(channels) == 1
        assert channels[0]["GuideName"] == "Test Channel"
        mock_get.assert_called_with("http://1.2.3.4/lineup.json", timeout=10)


def test_fetch_epg_integration_logic(temp_db_path, monkeypatch):
    """Test the logic in fetch_epg_data without hitting real API"""
    from hdhomerun_epg.config import settings

    monkeypatch.setattr(settings, "cache_db_path", temp_db_path)
    monkeypatch.setattr(settings, "cache_enabled", True)

    client = HDHomeRunClient("1.2.3.4")
    client.device_auth = "TEST"

    # Mock fetch_channels
    client.fetch_channels = MagicMock(return_value=[{"GuideNumber": "5.1"}])

    # Mock requests session
    with patch("requests.Session") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "GuideNumber": "5.1",
                "Guide": [{"Title": "Test Show", "StartTime": 1000000000}],
            }
        ]
        mock_session.get.return_value = mock_response

        # Mock datetime to control loop execution
        # Implementing a full mocked time loop is complex,
        # so here we just ensure the function runs without error using mocks
        # and hits the internal logic

        try:
            # Using a very small range to limit loops
            _ = client.fetch_epg_data(days=0, hours=1)
            # Note: logic might produce 0 results if days=0 or handle minimal loops
            # Ideally we'd mock time or pass explicit start/end if Client allowed
            pass
        except Exception as e:
            pytest.fail(f"fetch_epg_data raised exception: {e}")

    # Real integration tests are harder without extensive mocking of time
    # But basic structure is tested via mocks above


def test_fetch_epg_keeps_guide_channel_details(monkeypatch):
    from hdhomerun_epg.config import settings

    monkeypatch.setattr(settings, "cache_enabled", False)

    client = HDHomeRunClient("1.2.3.4")
    client.device_auth = "TEST"
    client.fetch_channels = MagicMock(
        return_value=[{"GuideNumber": "3", "GuideName": "RAI3RLO", "HD": 1}]
    )

    with patch("requests.Session") as mock_session_cls:
        mock_session_cls.return_value.get.return_value.json.return_value = [
            {
                "GuideNumber": "3",
                "GuideName": "RAI3RLO",
                "Affiliate": "Rai 3",
                "ImageURL": "http://img/rai3.png",
                "Guide": [{"Title": "TG3", "StartTime": 1000000000}],
            }
        ]
        epg = client.fetch_epg_data(days=1, hours=24)

    assert epg["channels"] == [
        {
            "GuideNumber": "3",
            "GuideName": "RAI3RLO",
            "HD": 1,
            "ImageURL": "http://img/rai3.png",
            "Affiliate": "Rai 3",
        }
    ]


@pytest.fixture
def guide_client(monkeypatch, mock_discovery_response):
    from hdhomerun_epg.config import settings

    monkeypatch.setattr(settings, "cache_enabled", False)
    client = HDHomeRunClient("1.2.3.4")
    client.device_auth = mock_discovery_response["DeviceAuth"]
    client.fetch_channels = MagicMock(
        return_value=[{"GuideNumber": "5.1"}, {"GuideNumber": "6.1"}]
    )
    # No call to SiliconDust's XMLTV feed from the tests that use the cache.
    client.fetch_official_details = MagicMock(return_value={})
    return client


def test_fetch_epg_deduplication(guide_client):
    programme = {"StartTime": 100, "EndTime": 200, "Title": "Test Show"}
    with patch("requests.Session") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "GuideNumber": "5.1",
                "Guide": [programme.copy(), dict(programme, StartTime=300)],
            },
            {"GuideNumber": "6.1", "Guide": [programme.copy()]},
        ]
        mock_session.get.return_value = mock_response
        result = guide_client.fetch_epg_data(days=1, hours=12)
        assert len(result["programmes"]) == 3
        assert mock_session.get.call_count == 2
        for call in mock_session.get.call_args_list:
            assert call.kwargs["verify"] is True
            assert call.kwargs["timeout"] == 30


@pytest.mark.parametrize(
    "error", [requests.Timeout, requests.HTTPError, requests.exceptions.SSLError]
)
def test_fetch_epg_request_error(guide_client, caplog, error):
    import traceback

    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"GuideNumber": "5.1", "Guide": [{"StartTime": 100, "Title": "Test Show"}]}
    ]
    with patch("requests.Session") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        mock_session.get.side_effect = [
            mock_response,
            error("https://provider.test/?DeviceAuth=" + guide_client.device_auth),
        ]
        with pytest.raises(RuntimeError, match="temporarily unavailable") as raised:
            guide_client.fetch_epg_data(days=1, hours=12)
    assert error.__name__ in caplog.text
    assert guide_client.device_auth not in "".join(
        traceback.format_exception(
            type(raised.value), raised.value, raised.value.__traceback__
        )
    )
    assert guide_client.device_auth not in caplog.text
    assert guide_client.device_auth not in str(raised.value)


def test_device_auth_logging(caplog, mock_discovery_response, mock_lineup_response):
    import logging

    caplog.set_level(logging.INFO, logger="hdhomerun_epg")
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.side_effect = [
            mock_discovery_response,
            mock_lineup_response,
        ]
        client = HDHomeRunClient("1.2.3.4")
        client.fetch_channels()
    assert mock_discovery_response["DeviceAuth"] not in caplog.text


def guide_response(start):
    response = MagicMock()
    response.json.return_value = [
        {
            "GuideNumber": "5.1",
            "Guide": [{"StartTime": start, "Title": f"Show {start}"}],
        }
    ]
    return response


def end_of_guide(client):
    """guide.php's answer for a Start past the end of its guide."""
    return requests.HTTPError(
        "400 Client Error for url: https://provider.test/?DeviceAuth="
        + client.device_auth,
        response=MagicMock(status_code=400),
    )


def test_end_of_guide_is_not_an_error(guide_client, caplog):
    import logging

    caplog.set_level(logging.INFO, logger="hdhomerun_epg")
    with patch("requests.Session") as mock_session_cls:
        mock_session_cls.return_value.get.side_effect = [
            guide_response(100),
            end_of_guide(guide_client),
        ]
        result = guide_client.fetch_epg_data(days=1, hours=12)

    assert [p["Title"] for p in result["programmes"]] == ["Show 100"]
    assert "guide ends" in caplog.text
    assert guide_client.device_auth not in caplog.text


def test_end_of_guide_on_the_first_chunk_is_an_error(guide_client):
    with patch("requests.Session") as mock_session_cls:
        mock_session_cls.return_value.get.side_effect = [end_of_guide(guide_client)]
        with pytest.raises(RuntimeError, match="temporarily unavailable"):
            guide_client.fetch_epg_data(days=1, hours=12)


def test_chunk_before_the_end_of_guide_is_not_cached(
    guide_client, temp_db_path, monkeypatch
):
    from hdhomerun_epg.cache import CacheManager
    from hdhomerun_epg.config import settings

    monkeypatch.setattr(settings, "cache_enabled", True)
    monkeypatch.setattr(settings, "cache_db_path", temp_db_path)
    with patch("requests.Session") as mock_session_cls:
        mock_session_cls.return_value.get.side_effect = [
            guide_response(100),
            guide_response(200),
            end_of_guide(guide_client),
        ]
        guide_client.fetch_epg_data(days=1, hours=8)

    # The second chunk runs past the end of the guide, so part of it is
    # missing; caching it would keep that gap for a whole TTL.
    assert len(CacheManager(temp_db_path).get_status()) == 1


def test_known_end_of_guide_is_not_requested_again(guide_client):
    with patch("requests.Session") as mock_session_cls:
        mock_get = mock_session_cls.return_value.get
        mock_get.side_effect = [guide_response(100), end_of_guide(guide_client)]
        guide_client.fetch_epg_data(days=1, hours=12)

        mock_get.reset_mock(side_effect=True)
        mock_get.side_effect = [guide_response(100)]
        result = guide_client.fetch_epg_data(days=1, hours=12)

    assert mock_get.call_count == 1
    assert [p["Title"] for p in result["programmes"]] == ["Show 100"]


def test_complete_guide_is_cached(guide_client, temp_db_path, monkeypatch):
    from hdhomerun_epg.cache import CacheManager
    from hdhomerun_epg.config import settings

    monkeypatch.setattr(settings, "cache_enabled", True)
    monkeypatch.setattr(settings, "cache_db_path", temp_db_path)
    with patch("requests.Session") as mock_session_cls:
        mock_session_cls.return_value.get.side_effect = [
            guide_response(100),
            guide_response(200),
        ]
        guide_client.fetch_epg_data(days=1, hours=12)

    assert len(CacheManager(temp_db_path).get_status()) == 2


def test_end_of_guide_is_asked_again_after_a_chunk(guide_client, monkeypatch):
    from hdhomerun_epg.client import HDHomeRunClient

    with patch("requests.Session") as mock_session_cls:
        mock_get = mock_session_cls.return_value.get
        mock_get.side_effect = [guide_response(100), end_of_guide(guide_client)]
        guide_client.fetch_epg_data(days=1, hours=12)

        # Twelve hours later the guide window has moved past that Start.
        refused_start, refused_at = HDHomeRunClient._guide_end
        HDHomeRunClient._guide_end = (refused_start, refused_at - 12 * 3600)
        mock_get.reset_mock(side_effect=True)
        mock_get.side_effect = [guide_response(100), guide_response(200)]
        result = guide_client.fetch_epg_data(days=1, hours=12)

    assert mock_get.call_count == 2
    assert len(result["programmes"]) == 2


def test_fetch_epg_adds_official_details(temp_db_path, monkeypatch):
    from hdhomerun_epg.config import settings

    monkeypatch.setattr(settings, "cache_enabled", True)
    monkeypatch.setattr(settings, "cache_db_path", temp_db_path)

    client = HDHomeRunClient("1.2.3.4")
    client.device_auth = "TEST"
    client.fetch_channels = MagicMock(
        return_value=[{"GuideNumber": "3", "GuideName": "RAI3RLO"}]
    )
    client.fetch_official_details = MagicMock(return_value=parse_details(OFFICIAL_FEED))

    with patch("requests.Session") as mock_session_cls:
        mock_session_cls.return_value.get.return_value.json.return_value = [
            {
                "GuideNumber": "3",
                "Guide": [{"Title": "1939-1945", "StartTime": OFFICIAL_START}],
            }
        ]
        epg = client.fetch_epg_data(days=1, hours=24)

    assert epg["programmes"][0]["Synopsis"] == "Il 10 giugno 1940."


def official_client():
    client = HDHomeRunClient("1.2.3.4")
    client.device_auth = "SECRET"
    return client


def test_official_details_come_from_the_cache_while_fresh(temp_db_path):
    cache = CacheManager(temp_db_path)
    cache.save_feed(
        "official_xmltv", {"3|1": {"Synopsis": "x"}}, expires_at=int(time.time()) + 60
    )

    with patch("requests.get") as mock_get:
        assert official_client().fetch_official_details(cache) == {
            "3|1": {"Synopsis": "x"}
        }
    mock_get.assert_not_called()


def test_official_details_refresh_every_20_to_28_hours(temp_db_path):
    cache = CacheManager(temp_db_path)

    with patch("requests.get") as mock_get:
        mock_get.return_value.content = OFFICIAL_FEED
        details = official_client().fetch_official_details(cache)

    assert f"3|{OFFICIAL_START}" in details
    mock_get.assert_called_once_with(
        "https://api.hdhomerun.com/api/xmltv",
        params={"DeviceAuth": "SECRET"},
        timeout=60,
    )
    expires_in = cache.get_feed("official_xmltv")["expires_at"] - time.time()
    assert 20 * 3600 - 5 <= expires_in <= 28 * 3600


def test_official_feed_failure_keeps_old_details_and_hides_device_auth(
    temp_db_path, caplog
):
    cache = CacheManager(temp_db_path)
    cache.save_feed("official_xmltv", {"3|1": {"Synopsis": "old"}}, expires_at=1)
    error = requests.ConnectionError(
        "Max retries exceeded: /api/xmltv?DeviceAuth=SECRET"
    )

    with patch("requests.get", side_effect=error):
        details = official_client().fetch_official_details(cache)

    assert details == {"3|1": {"Synopsis": "old"}}
    assert "ConnectionError" in caplog.text
    assert "SECRET" not in caplog.text
    # Retry in an hour, not on every request.
    expires_in = cache.get_feed("official_xmltv")["expires_at"] - time.time()
    assert 3600 - 5 <= expires_in <= 3600
