import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_search_returns_results(client):
    r = client.get("/search?q=наушники")
    assert r.status_code == 200
    body = r.json()
    assert "results" in body


def test_register_login_create_review(client):
    email = "tester_unique@example.com"
    client.post("/auth/register", json={"email": email, "password": "secret123"})
    r = client.post("/auth/login", data={"username": email, "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "product_id": 1,
        "platform_id": 1,
        "seller_id": 1,
        "score_service": 5,
        "score_seller": 4,
        "score_product": 5,
        "score_delivery": 3,
        "comment_text": "Тестовый отзыв",
    }
    r = client.post("/reviews", json=payload, headers=headers)
    assert r.status_code == 201
    assert abs(r.json()["score_total"] - 4.25) < 1e-6
