from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_get_cars():
    response = client.get("/api/cars")
    assert response.status_code == 200
    cars = response.json()
    assert all(['doors' in d for d in cars])
    assert all(['size' in s for s in cars])
