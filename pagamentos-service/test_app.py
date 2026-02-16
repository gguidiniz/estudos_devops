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
    assert resp.get_json()["service"] == "pagamentos-service"


def test_process_payment(client):
    resp = client.post("/payments", json={"order_id": 1, "amount": 100.00})
    assert resp.status_code in [201, 422]
    data = resp.get_json()
    assert data["order_id"] == 1
    assert data["amount"] == 100.00
    assert data["status"] in ["approved", "declined"]


def test_process_payment_missing_fields(client):
    resp = client.post("/payments", json={"order_id": 1})
    assert resp.status_code == 400


def test_get_payment(client):
    client.post("/payments", json={"order_id": 1, "amount": 50.00})
    resp = client.get("/payments/1")
    assert resp.status_code == 200
    assert resp.get_json()["order_id"] == 1


def test_payment_not_found(client):
    resp = client.get("/payments/999")
    assert resp.status_code == 404


def test_list_payments(client):
    client.post("/payments", json={"order_id": 1, "amount": 50.00})
    client.post("/payments", json={"order_id": 2, "amount": 75.00})
    resp = client.get("/payments")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2
