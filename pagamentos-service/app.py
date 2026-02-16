import os
import random
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pagamentos_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), default="credit_card")
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "amount": self.amount,
            "method": self.method,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "pagamentos-service"})


@app.route("/payments", methods=["POST"])
def process_payment():
    data = request.get_json()
    if not data or not data.get("order_id") or not data.get("amount"):
        return jsonify({"error": "Campos 'order_id' e 'amount' são obrigatórios"}), 400

    approved = random.random() < 0.9
    status = "approved" if approved else "declined"

    payment = Payment(
        order_id=data["order_id"],
        amount=data["amount"],
        method=data.get("method", "credit_card"),
        status=status,
    )
    db.session.add(payment)
    db.session.commit()

    status_code = 201 if approved else 422
    return jsonify(payment.to_dict()), status_code


@app.route("/payments/<int:payment_id>", methods=["GET"])
def get_payment(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        return jsonify({"error": "Pagamento não encontrado"}), 404
    return jsonify(payment.to_dict())


@app.route("/payments", methods=["GET"])
def list_payments():
    payments = Payment.query.all()
    return jsonify([p.to_dict() for p in payments])


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
