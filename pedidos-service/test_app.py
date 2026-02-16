import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db


@pytest.fixture
def client():
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["service"] == "pedidos-service"


def test_list_orders_empty(client):
    resp = client.get("/orders")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_order_missing_fields(client):
    resp = client.post("/orders", json={"customer": "João"})
    assert resp.status_code == 400


def test_get_order_not_found(client):
    resp = client.get("/orders/999")
    assert resp.status_code == 404
