import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    yield app.test_client()


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "Pedidos Veloz" in data["service"]
    assert "/orders" in data["endpoints"]
