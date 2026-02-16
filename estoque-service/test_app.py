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
    assert resp.get_json()["service"] == "estoque-service"


def test_create_item(client):
    resp = client.post("/items", json={"name": "Camiseta", "quantity": 50, "price": 59.90})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Camiseta"
    assert data["quantity"] == 50


def test_list_items(client):
    client.post("/items", json={"name": "Tênis", "quantity": 10, "price": 199.90})
    resp = client.get("/items")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_get_item(client):
    client.post("/items", json={"name": "Boné", "quantity": 30, "price": 39.90})
    resp = client.get("/items/1")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Boné"


def test_item_not_found(client):
    resp = client.get("/items/999")
    assert resp.status_code == 404


def test_reserve_stock(client):
    client.post("/items", json={"name": "Mochila", "quantity": 5, "price": 120.00})
    resp = client.patch("/items/1/reserve", json={"quantity": 2})
    assert resp.status_code == 200
    assert resp.get_json()["item"]["quantity"] == 3


def test_reserve_insufficient_stock(client):
    client.post("/items", json={"name": "Relógio", "quantity": 1, "price": 500.00})
    resp = client.patch("/items/1/reserve", json={"quantity": 5})
    assert resp.status_code == 409
