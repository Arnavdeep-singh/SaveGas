import pytest
from sqlalchemy.exc import OperationalError
from database import get_db
from main import app

STATION = {"name": "Shell Kingsway", "brand": "Shell", "latitude": 49.232, "longitude": -123.023}


def test_empty_list(client):
    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_retrieve_stations(client):
    created = client.post("/api/stations", json=STATION)
    assert created.status_code == 201
    assert created.json() == {"id": 1, **STATION}
    second = client.post("/api/stations", json={**STATION, "name": "Chevron Lougheed", "brand": "Chevron"})
    assert second.status_code == 201
    response = client.get("/api/stations")
    assert response.status_code == 200
    assert response.json() == [created.json(), second.json()]


@pytest.mark.parametrize("changes", [
    {"name": "   "}, {"brand": ""}, {"name": "a" * 101}, {"brand": "a" * 101},
    {"latitude": 90.1}, {"latitude": -90.1}, {"longitude": 180.1}, {"longitude": -180.1},
    {"latitude": "NaN"}, {"longitude": "Infinity"}, {"id": 123},
])
def test_invalid_station_is_not_saved(client, changes):
    assert client.post("/api/stations", json={**STATION, **changes}).status_code == 422
    assert client.get("/api/stations").json() == []


def test_missing_field(client):
    assert client.post("/api/stations", json={"name": "Shell"}).status_code == 422


def test_whitespace_and_coordinate_boundaries(client):
    response = client.post("/api/stations", json={**STATION, "name": " Shell ", "latitude": -90, "longitude": 180})
    assert response.status_code == 201
    assert response.json()["name"] == "Shell"


@pytest.mark.parametrize("method", ["get", "post"])
def test_database_failure_returns_503(client, method):
    class UnavailableSession:
        rolled_back = False

        def add(self, station):
            pass

        def commit(self):
            raise OperationalError("", {}, Exception("offline"))

        def scalars(self, query):
            raise OperationalError("", {}, Exception("offline"))

        def rollback(self):
            self.rolled_back = True

    db = UnavailableSession()
    app.dependency_overrides[get_db] = lambda: db
    if method == "post":
        response = client.post("/api/stations", json=STATION)
        assert db.rolled_back
    else:
        response = client.get("/api/stations")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_health_and_cors(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    response = client.options("/api/stations", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
