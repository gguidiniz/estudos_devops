import os
import requests as http_client
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pedidos_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

ESTOQUE_SERVICE_URL = os.getenv("ESTOQUE_SERVICE_URL", "http://localhost:5003")
PAGAMENTOS_SERVICE_URL = os.getenv("PAGAMENTOS_SERVICE_URL", "http://localhost:5002")

db = SQLAlchemy(app)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="created")
    total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    items = db.relationship("OrderItem", backref="order", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "customer": self.customer,
            "status": self.status,
            "total": self.total,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(200), default="")
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
        }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "pedidos-service"})


@app.route("/orders", methods=["GET"])
def list_orders():
    orders = Order.query.all()
    return jsonify([o.to_dict() for o in orders])


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Pedido não encontrado"}), 404
    return jsonify(order.to_dict())


@app.route("/orders", methods=["POST"])
def create_order():
    """
    Expected body:
    {
        "customer": "João Silva",
        "items": [
            {"item_id": 1, "quantity": 2},
            {"item_id": 3, "quantity": 1}
        ]
    }
    """
    data = request.get_json()
    if not data or not data.get("customer") or not data.get("items"):
        return jsonify({"error": "Campos 'customer' e 'items' são obrigatórios"}), 400

    total = 0.0
    reserved_items = []

    for item_req in data["items"]:
        item_id = item_req.get("item_id")
        quantity = item_req.get("quantity", 1)

        try:
            resp = http_client.get(f"{ESTOQUE_SERVICE_URL}/items/{item_id}", timeout=5)
            if resp.status_code != 200:
                return jsonify({"error": f"Item {item_id} não encontrado no estoque"}), 404

            item_info = resp.json()

            resp_reserve = http_client.patch(
                f"{ESTOQUE_SERVICE_URL}/items/{item_id}/reserve",
                json={"quantity": quantity},
                timeout=5,
            )
            if resp_reserve.status_code != 200:
                return jsonify({
                    "error": f"Falha ao reservar item {item_id}",
                    "detail": resp_reserve.json(),
                }), 409

            subtotal = item_info["price"] * quantity
            total += subtotal
            reserved_items.append({
                "item_id": item_id,
                "item_name": item_info["name"],
                "quantity": quantity,
                "unit_price": item_info["price"],
            })

        except http_client.exceptions.RequestException as e:
            return jsonify({"error": "Serviço de estoque indisponível", "detail": str(e)}), 503

    order = Order(customer=data["customer"], total=total, status="stock_reserved")
    db.session.add(order)
    db.session.flush()

    for item_data in reserved_items:
        order_item = OrderItem(order_id=order.id, **item_data)
        db.session.add(order_item)

    db.session.commit()

    try:
        resp_payment = http_client.post(
            f"{PAGAMENTOS_SERVICE_URL}/payments",
            json={"order_id": order.id, "amount": total},
            timeout=10,
        )
        payment_data = resp_payment.json()

        if resp_payment.status_code == 201:
            order.status = "paid"
        else:
            order.status = "payment_declined"

        db.session.commit()

    except http_client.exceptions.RequestException as e:
        order.status = "payment_error"
        db.session.commit()
        return jsonify({
            "order": order.to_dict(),
            "warning": "Pedido criado, mas houve erro no pagamento",
            "detail": str(e),
        }), 207

    return jsonify({
        "order": order.to_dict(),
        "payment": payment_data,
    }), 201


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
