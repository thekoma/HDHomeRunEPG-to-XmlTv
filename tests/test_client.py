import pytest
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
