from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from hdhomerun_epg.config import settings

client = TestClient(app)


def test_delete_cache(monkeypatch, temp_db_path):
    monkeypatch.setattr(settings, "cache_db_path", temp_db_path)
    # Ensure it doesn't fail if DB doesn't exist
    response = client.delete("/cache")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Cache cleared"}


def test_get_epg_error_handling(monkeypatch):
    """Test that failed client fetch returns 500"""
    with patch("hdhomerun_epg.client.HDHomeRunClient.fetch_epg_data") as mock_fetch:
        mock_fetch.side_effect = Exception("Mocked Failure")
        response = client.get("/epg.xml")
        assert response.status_code == 500
        assert "Error generating EPG" in response.text


def test_cache_status_endpoint(monkeypatch, temp_db_path):
    monkeypatch.setattr(settings, "cache_db_path", temp_db_path)
    response = client.get("/cache")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "HDHomeRun EPG Status" in response.text


def test_root_json_status(monkeypatch, temp_db_path):
    monkeypatch.setattr(settings, "cache_db_path", temp_db_path)
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert "cache_entries" in response.json()


def test_tv_guide_endpoint(monkeypatch):
    # Mock client.fetch_epg_data to avoid API calls and speed up test
    from hdhomerun_epg import client as lib_client

    def mock_fetch(self, days=1, hours=4):
        import time

        now = int(time.time())
        return {
            "channels": [{"GuideNumber": "1", "GuideName": "TEST", "ImageURL": ""}],
            "programmes": [
                {
                    "GuideNumber": "1",
                    "StartTime": now + 60,
                    "EndTime": now + 3660,
                    "Title": "Test Prog",
                }
            ],
        }

    monkeypatch.setattr(lib_client.HDHomeRunClient, "fetch_epg_data", mock_fetch)

    response = client.get("/guide")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TV Guide" in response.text
    assert "Test Prog" in response.text


def test_get_epg_partial_failure(monkeypatch, caplog):
    import requests
    from hdhomerun_epg.client import HDHomeRunClient

    monkeypatch.setattr(settings, "epg_days", 1)
    monkeypatch.setattr(settings, "epg_hours", 12)
    monkeypatch.setattr(settings, "cache_enabled", False)
    monkeypatch.setattr(
        HDHomeRunClient,
        "discover_device_auth",
        lambda self: setattr(self, "device_auth", "PRIVATE_DEVICE_AUTH"),
    )
    monkeypatch.setattr(
        HDHomeRunClient, "fetch_channels", lambda self: [{"GuideNumber": "5.1"}]
    )
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "GuideNumber": "5.1",
            "Guide": [{"StartTime": 100, "EndTime": 200, "Title": "Test Show"}],
        }
    ]
    with patch("requests.Session") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        mock_session.get.side_effect = [
            mock_response,
            requests.Timeout("https://provider.test/?DeviceAuth=PRIVATE_DEVICE_AUTH"),
        ]
        response = client.get("/epg.xml")
    assert response.status_code == 500
    assert "<tv" not in response.text
    assert "PRIVATE_DEVICE_AUTH" not in response.text
    assert "PRIVATE_DEVICE_AUTH" not in caplog.text
