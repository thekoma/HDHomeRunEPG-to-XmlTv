import pytest
import requests
from unittest.mock import MagicMock, patch
from hdhomerun_epg.client import HDHomeRunClient


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


@pytest.fixture
def guide_client(monkeypatch, mock_discovery_response):
    from hdhomerun_epg.config import settings

    monkeypatch.setattr(settings, "cache_enabled", False)
    client = HDHomeRunClient("1.2.3.4")
    client.device_auth = mock_discovery_response["DeviceAuth"]
    client.fetch_channels = MagicMock(
        return_value=[{"GuideNumber": "5.1"}, {"GuideNumber": "6.1"}]
    )
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
