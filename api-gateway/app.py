import os
import requests as http_client
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

SERVICES = {
    "pedidos": os.getenv("PEDIDOS_SERVICE_URL", "http://localhost:5001"),
    "pagamentos": os.getenv("PAGAMENTOS_SERVICE_URL", "http://localhost:5002"),
    "estoque": os.getenv("ESTOQUE_SERVICE_URL", "http://localhost:5003"),
}


def proxy_request(service_name, path):
    service_url = SERVICES.get(service_name)
    if not service_url:
        return jsonify({"error": f"Serviço '{service_name}' não encontrado"}), 404

    target_url = f"{service_url}/{path}"


    # Headers to forward (creating a clean dict to avoid issues)
    forward_headers = {key: value for key, value in request.headers if key.lower() != "host"}

    try:
        resp = http_client.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            data=request.get_data(),
            params=request.args,
            timeout=15,
        )

        return Response(
            response=resp.content,
            status=resp.status_code,
            headers=dict(resp.headers),
        )

    except http_client.exceptions.RequestException as e:
        print(f"Erro ao conectar com {service_name}: {e}", flush=True)
        return jsonify({"error": f"Serviço '{service_name}' indisponível ou erro de conexão", "details": str(e)}), 503


@app.route("/health", methods=["GET"])
def health():
    statuses = {}
    for name, url in SERVICES.items():
        try:
            resp = http_client.get(f"{url}/health", timeout=3)
            statuses[name] = "healthy" if resp.status_code == 200 else "unhealthy"
        except http_client.exceptions.RequestException:
            statuses[name] = "unreachable"

    all_healthy = all(s == "healthy" for s in statuses.values())
    return jsonify({
        "status": "healthy" if all_healthy else "degraded",
        "service": "api-gateway",
        "backends": statuses,
    }), 200 if all_healthy else 207


@app.route("/orders", defaults={"path": "orders"}, methods=["GET", "POST"])
@app.route("/orders/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy_orders(path):
    if not path.startswith("orders"):
        path = f"orders/{path}"
    return proxy_request("pedidos", path)


@app.route("/payments", defaults={"path": "payments"}, methods=["GET", "POST"])
@app.route("/payments/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy_payments(path):
    if not path.startswith("payments"):
        path = f"payments/{path}"
    return proxy_request("pagamentos", path)


@app.route("/items", defaults={"path": "items"}, methods=["GET", "POST"])
@app.route("/items/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy_inventory(path):
    if not path.startswith("items"):
        path = f"items/{path}"
    return proxy_request("estoque", path)


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "Pedidos Veloz - API Gateway",
        "version": "1.0.0",
        "endpoints": ["/orders", "/payments", "/items", "/health"],
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
