import pytest
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
