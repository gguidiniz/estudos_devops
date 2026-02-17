
## 1. Abertura (0:00 – 0:20)

**Tela:**  Mostrar o README do repositório no GitHub.

> "Olá! Eu sou [seu nome], e neste vídeo vou apresentar o projeto Pedidos Veloz — uma plataforma de pedidos construída com microsserviços, Docker, Kubernetes e CI/CD."

----------

## 2. Arquitetura (0:20 – 0:50)

**Tela:**  Mostrar a estrutura de pastas do projeto no VS Code.

> "A aplicação é composta por 4 microsserviços em Python com Flask: API Gateway, Serviço de Pedidos, Pagamentos e Estoque, cada um com seu banco de dados no PostgreSQL. O Gateway atua como ponto de entrada único, roteando as requisições para os serviços internos."

----------

## 3. Docker e Docker Compose (0:50 – 1:20)

**Tela:** Mostrar o Dockerfile e rodar `docker compose up --build`. Mostrar o health check:

```powershell
curl.exe http://localhost:5000/health
```

> "Cada serviço tem seu Dockerfile com multi-stage build — um estágio instala dependências, outro roda a aplicação com usuário não-root para segurança. Com um único `docker compose up`, subimos todos os serviços, o PostgreSQL e a stack de monitoramento."

----------

## 4. Demonstração Funcional (1:20 – 1:50)

**Tela:** Rodar os comandos no terminal:
```powershell
curl.exe -X POST http://localhost:5000/items -H "Content-Type: application/json" -d '{"name":"Camiseta","quantity":50,"price":59.90}'
curl.exe -X POST http://localhost:5000/orders -H "Content-Type: application/json" -d '{"customer":"Joao","items":[{"item_id":1,"quantity":2}]}'
curl.exe http://localhost:5000/orders
```

> "Vou demonstrar o fluxo completo: criar um item no estoque, fazer um pedido e ver o pagamento sendo processado."

----------

## 5. Testes e CI/CD (1:50 – 2:30)

**Tela:**  Mostrar o pipeline verde no GitHub Actions. Abrir o arquivo  `ci.yml`  brevemente.

> "O projeto tem testes unitários para cada serviço, rodando via Docker. No GitHub Actions, o pipeline executa em 4 estágios: lint com flake8, testes com pytest, build e push das imagens Docker para o GitHub Container Registry, e deploy no Kubernetes. Tudo roda em paralelo graças à matrix strategy."

----------

## 6. Kubernetes e Escala (2:30 – 3:10)

**Tela:**  Mostrar os arquivos em  `k8s/`  — focar no  `hpa.yml`  e em um Deployment.

> "Para produção, temos manifests Kubernetes com Deployments de 2+ réplicas, rolling updates com zero-downtime, health checks nos pods, e HPA — Horizontal Pod Autoscaler — que escala automaticamente quando CPU passa de 70%. Secrets e ConfigMaps separam credenciais de configurações."

----------

## 7. Observabilidade e IaC (3:10 – 3:40)

**Tela:**  Abrir o Grafana (`localhost:3000`) → Connections → Data sources (mostrar Prometheus e Loki configurados). Depois ir em Explore → selecionar Prometheus → digitar  `up`  → Run query (mostrar os 4 serviços listados). Por último, mostrar brevemente o  `terraform/cluster.tf`  no VS Code.

> "No Grafana, temos dois datasources configurados: Prometheus para métricas e Loki para logs. Aqui no Explore, rodando a query 'up' no Prometheus, vemos os nossos 4 serviços sendo monitorados. A infraestrutura do cluster é declarada como código com Terraform, usando módulos oficiais da AWS para VPC e EKS."

----------

## 8. Encerramento (3:40 – 4:00)

**Tela:**  Voltar ao README do repositório.

> "Em resumo: microsserviços independentes, containerizados com boas práticas de segurança, orquestrados por Kubernetes com escala automática, entregues por um pipeline CI/CD completo e monitorados em tempo real. Obrigado!"