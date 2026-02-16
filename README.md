# Pedidos Veloz — Cloud DevOps

Plataforma de pedidos em microsserviços com Docker Compose, Kubernetes, CI/CD e observabilidade.

## Arquitetura

```
Cliente → API Gateway (:5000) → Pedidos Service (:5001) → Estoque Service (:5003)
                                                        → Pagamentos Service (:5002)
                                                        
Todos os serviços → PostgreSQL (:5432)
```

| Serviço | Descrição | Porta |
|---|---|---|
| **api-gateway** | Reverse proxy para os microsserviços | 5000 |
| **pedidos-service** | Criação e consulta de pedidos | 5001 |
| **pagamentos-service** | Simulação de processamento de pagamentos | 5002 |
| **estoque-service** | CRUD de itens e reserva de estoque | 5003 |
| **postgres** | Banco de dados PostgreSQL 16 | 5432 |
| **prometheus** | Coleta de métricas | 9090 |
| **grafana** | Dashboards de observabilidade | 3000 |
| **loki** | Agregação de logs | 3100 |

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (para deploy em Kubernetes)
- [Terraform](https://developer.hashicorp.com/terraform/install) (para IaC)

## Executar Localmente

```bash
# Subir todos os serviços com um único comando
docker compose up --build

# Verificar que tudo está rodando
curl http://localhost:5000/health
```

### Endpoints disponíveis

```bash
# Listar itens do estoque
curl http://localhost:5000/items

# Criar um item
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Camiseta", "quantity": 50, "price": 59.90}'

# Criar um pedido
curl -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer": "João Silva", "items": [{"item_id": 1, "quantity": 2}]}'

# Consultar pedidos
curl http://localhost:5000/orders
```

### Monitoramento

- **Grafana**: http://localhost:3000 (usuário: `admin`, senha: `admin`)
- **Prometheus**: http://localhost:9090

## Testes

```bash
# Executar testes de cada serviço via Docker (sem precisar de Python local)
docker compose run --rm --no-deps --user root -e DATABASE_URL=sqlite:///test.db -v ./estoque-service/test_app.py:/app/test_app.py estoque-service sh -c "pip install pytest && pytest test_app.py -v"
docker compose run --rm --no-deps --user root -e DATABASE_URL=sqlite:///test.db -v ./pagamentos-service/test_app.py:/app/test_app.py pagamentos-service sh -c "pip install pytest && pytest test_app.py -v"
docker compose run --rm --no-deps --user root -e DATABASE_URL=sqlite:///test.db -v ./pedidos-service/test_app.py:/app/test_app.py pedidos-service sh -c "pip install pytest && pytest test_app.py -v"
docker compose run --rm --no-deps --user root -e DATABASE_URL=sqlite:///test.db -v ./api-gateway/test_app.py:/app/test_app.py api-gateway sh -c "pip install pytest && pytest test_app.py -v"
```

> Os testes também rodam automaticamente no CI (GitHub Actions) a cada push/PR.

## Deploy em Kubernetes

```bash
# Aplicar os manifests na ordem
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/postgres.yml
kubectl apply -f k8s/estoque-service.yml
kubectl apply -f k8s/pagamentos-service.yml
kubectl apply -f k8s/pedidos-service.yml
kubectl apply -f k8s/api-gateway.yml
kubectl apply -f k8s/hpa.yml

# Verificar status
kubectl get pods -n pedidos-veloz
kubectl get svc -n pedidos-veloz
kubectl get hpa -n pedidos-veloz
```

## CI/CD

O pipeline (`.github/workflows/ci.yml`) executa automaticamente em push/PR na `main`:

1. **Lint** — flake8 em todos os serviços
2. **Test** — pytest em todos os serviços
3. **Build & Push** — imagens Docker para GitHub Container Registry
4. **Deploy** — aplica manifests e faz rolling restart no Kubernetes

## Infraestrutura como Código

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Estrutura do Projeto

```
├── api-gateway/           # Reverse proxy (Flask)
├── pedidos-service/       # Serviço de pedidos (Flask + SQLAlchemy)
├── pagamentos-service/    # Serviço de pagamentos (Flask + SQLAlchemy)
├── estoque-service/       # Serviço de estoque (Flask + SQLAlchemy)
├── k8s/                   # Manifests Kubernetes
│   ├── namespace.yml
│   ├── secrets.yml
│   ├── configmap.yml
│   ├── postgres.yml
│   ├── estoque-service.yml
│   ├── pagamentos-service.yml
│   ├── pedidos-service.yml
│   ├── api-gateway.yml
│   └── hpa.yml
├── monitoring/            # Configurações de observabilidade
│   ├── prometheus.yml
│   ├── loki.yml
│   └── grafana/
├── terraform/             # IaC (AWS EKS)
├── .github/workflows/     # Pipeline CI/CD
├── docker-compose.yml     # Ambiente local
└── init-db.sql            # Inicialização do PostgreSQL
```

## Stack Tecnológica

- **Linguagem**: Python 3.12 + Flask
- **Banco de dados**: PostgreSQL 16
- **Contêineres**: Docker (multi-stage builds)
- **Orquestração local**: Docker Compose
- **Orquestração produção**: Kubernetes
- **CI/CD**: GitHub Actions
- **Observabilidade**: Prometheus + Grafana + Loki
- **IaC**: Terraform (AWS EKS)
- **Deploy**: Rolling Update (zero-downtime)
- **Escala**: HPA (CPU 70% / Memory 80%)
