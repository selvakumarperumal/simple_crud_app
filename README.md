# Simple CRUD App

FastAPI CRUD application with SQLModel, asyncpg, Pydantic, Docker, and Helm.

## Tech Stack

- **FastAPI** — async web framework
- **SQLModel** — ORM (SQLAlchemy + Pydantic)
- **asyncpg** — async PostgreSQL driver
- **Pydantic** — data validation
- **Docker** — containerization
- **Helm** — Kubernetes deployment

## Project Structure

```
app/
├── __init__.py
├── config.py         # Settings via pydantic-settings
├── database.py       # Async engine & session
├── models.py         # SQLModel table + request/response schemas
├── routes.py         # CRUD endpoints
└── main.py           # FastAPI app entrypoint
helm/
└── simple-crud-app/  # Helm chart
Dockerfile
docker-compose.yml
pyproject.toml
```

## Quick Start (Docker Compose)

```bash
docker compose up --build
```

API available at http://localhost:8000
Docs at http://localhost:8000/docs

## Local Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Start PostgreSQL (e.g. via docker)
docker compose up db -d

# Run the app
uvicorn app.main:app --reload
```

## API Endpoints

| Method   | Path                      | Description      |
|----------|---------------------------|------------------|
| `GET`    | `/health`                 | Health check     |
| `POST`   | `/api/v1/items/`          | Create item      |
| `GET`    | `/api/v1/items/`          | List items       |
| `GET`    | `/api/v1/items/{id}`      | Get item by ID   |
| `PATCH`  | `/api/v1/items/{id}`      | Update item      |
| `DELETE` | `/api/v1/items/{id}`      | Delete item      |

## Deploy on Minikube

### Prerequisites

- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [helm](https://helm.sh/docs/intro/install/)

### 1. Start Minikube

```bash
minikube start --cpus 4 --memory 4096 --driver=docker
```

### 2. Install CloudNativePG Operator

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/main/releases/cnpg-1.25.0.yaml

# Wait for the operator to be ready
kubectl wait --for=condition=Available deployment/cnpg-controller-manager \
  -n cnpg-system --timeout=120s
```

### 3. Build the Docker Image Inside Minikube

```bash
# Point your shell to minikube's Docker daemon
eval $(minikube docker-env)

# Build the image (now available inside minikube)
docker build -t simple-crud-app:latest .
```

### 4. Deploy with Helm

```bash
cd helm/simple-crud-app

helm install crud-app . \
  -n crud --create-namespace \
  --set image.pullPolicy=Never
```

> `image.pullPolicy=Never` ensures Kubernetes uses the locally built image
> instead of trying to pull from a remote registry.

### 5. Verify the Deployment

```bash
# Check CNPG cluster status
kubectl get cluster -n crud

# Check pods are running
kubectl get pods -n crud

# Wait for the app to be ready
kubectl wait --for=condition=Available deployment/crud-app-simple-crud-app \
  -n crud --timeout=180s
```

### 6. Access the API

```bash
# Port-forward to access locally
kubectl port-forward svc/crud-app-simple-crud-app 8000:80 -n crud
```

API available at http://localhost:8000
Swagger docs at http://localhost:8000/docs

Alternatively, use minikube service:

```bash
minikube service crud-app-simple-crud-app -n crud
```

### 7. Test It

```bash
# Create an item
curl -X POST http://localhost:8000/api/v1/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "description": "A test widget", "price": 9.99}'

# List items
curl http://localhost:8000/api/v1/items/
```

### Cleanup

```bash
helm uninstall crud-app -n crud
kubectl delete namespace crud
minikube stop
```

## Helm Deployment (General)

```bash
cd helm/simple-crud-app
helm install crud-app . -n crud --create-namespace
```

Override values:

```bash
helm install crud-app . \
  --set image.repository=myregistry/simple-crud-app \
  --set image.tag=v0.1.0 \
  --set ingress.enabled=true
```