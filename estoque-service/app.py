import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/estoque_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), default="")
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "quantity": self.quantity,
            "price": self.price,
            "created_at": self.created_at.isoformat(),
        }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "estoque-service"})


@app.route("/items", methods=["GET"])
def list_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])


@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = db.session.get(Item, item_id)
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404
    return jsonify(item.to_dict())


@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Campo 'name' é obrigatório"}), 400

    item = Item(
        name=data["name"],
        description=data.get("description", ""),
        quantity=data.get("quantity", 0),
        price=data.get("price", 0.0),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@app.route("/items/<int:item_id>/reserve", methods=["PATCH"])
def reserve_item(item_id):
    item = db.session.get(Item, item_id)
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    data = request.get_json()
    quantity = data.get("quantity", 1)

    if item.quantity < quantity:
        return jsonify({"error": "Estoque insuficiente", "available": item.quantity}), 409

    item.quantity -= quantity
    db.session.commit()
    return jsonify({"message": "Estoque reservado", "item": item.to_dict()})


@app.route("/items/<int:item_id>/write-off", methods=["PATCH"])
def write_off_item(item_id):
    item = db.session.get(Item, item_id)
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    return jsonify({"message": "Baixa confirmada", "item": item.to_dict()})


with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}", flush=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
