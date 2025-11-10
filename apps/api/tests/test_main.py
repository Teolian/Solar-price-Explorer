import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_healthcheck():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["timezone"] == "Asia/Tokyo"

def test_get_areas():
    response = client.get("/api/areas")
    assert response.status_code == 200
    data = response.json()
    assert "areas" in data
    assert len(data["areas"]) == 9
    assert "TOKYO" in data["areas"]

def test_get_prices_missing_area():
    response = client.get("/api/prices")
    assert response.status_code == 422  # Validation error

def test_get_radiation_missing_area():
    response = client.get("/api/radiation")
    assert response.status_code == 422  # Validation error
