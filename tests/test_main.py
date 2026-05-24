from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI in devcontainer"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_read_domains() -> None:
    response = client.get("/domains")
    assert response.status_code == 200
    assert response.json() == ["a.com", "b.com", "c.com"]


def test_check_email_ok() -> None:
    response = client.post("/check", json={"email": "user@example.com", "code": "001"})
    assert response.status_code == 200
    assert response.json() == {"result": "OK"}


def test_check_email_ng() -> None:
    response = client.post("/check", json={"email": "example.com", "code": "001"})
    assert response.status_code == 200
    assert response.json() == {"result": "NG"}
