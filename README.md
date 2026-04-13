# Simple CRUD App

FastAPI CRUD application with SQLModel, asyncpg, Pydantic, Docker, and Helm.

## Tech Stack

- **FastAPI** — async web framework
- **SQLModel** — ORM (SQLAlchemy + Pydantic)
- **asyncpg** — async PostgreSQL driver
- **Pydantic** — data validation
- **Docker** — containerization
- **Helm** — Kubernetes deployment
- **CloudNativePG** — PostgreSQL operator for Kubernetes
- **Prometheus** — metrics collection
- **Grafana** — dashboards & visualization
- **Loki** — log aggregation

## Project Structure

```
app/
├── __init__.py
├── config.py         # Settings via pydantic-settings
├── database.py       # Async engine & session
├── models.py         # SQLModel table + request/response schemas
├── routes.py         # CRUD endpoints
└── main.py           # FastAPI app entrypoint + /metrics
helm/
└── simple-crud-app/
    ├── Chart.yaml
    ├── values.yaml
    ├── values-monitoring.yaml   # Monitoring overlay
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        ├── hpa.yaml
        ├── cnpg-cluster.yaml      # CloudNativePG Cluster
        ├── servicemonitor.yaml    # Prometheus ServiceMonitor
        ├── loki-datasource.yaml   # Loki datasource for Grafana
        └── grafana-dashboard.yaml # Grafana dashboard ConfigMap
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
| `GET`    | `/metrics`                | Prometheus metrics |

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

The [CloudNativePG operator](https://cloudnative-pg.io/) must be installed in the cluster before deploying.

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.0.yaml

kubectl wait --for=condition=Available deployment/cnpg-controller-manager \
  -n cnpg-system --timeout=120s
```

### 3. Install Monitoring Stack (Prometheus + Grafana + Loki)

```bash
# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create monitoring namespace
kubectl create namespace monitoring

# Install kube-prometheus-stack (Prometheus + Grafana)
helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=admin123 \
  --set prometheus.prometheusSpec.scrapeInterval=15s \
  --set grafana.service.type=NodePort \
  --set grafana.sidecar.dashboards.enabled=true \
  --set grafana.sidecar.dashboards.searchNamespace=ALL \
  --set grafana.sidecar.datasources.enabled=true \
  --set grafana.sidecar.datasources.searchNamespace=ALL

# Wait for Prometheus operator
kubectl wait --for=condition=Available deployment/prometheus-stack-kube-prom-operator \
  --namespace monitoring --timeout=120s

# Install Loki + Promtail (log aggregation)
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set grafana.enabled=false \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=false
```

Verify monitoring pods are running:

```bash
kubectl get pods -n monitoring

# Expected pods:
# prometheus-stack-grafana-*
# prometheus-stack-kube-prom-prometheus-*
# prometheus-stack-kube-prom-alertmanager-*
# loki-0
# loki-promtail-*  (one per node)
```

### 4. Build the Docker Image Inside Minikube

```bash
eval $(minikube docker-env)
docker build -t simple-crud-app:latest .
```

### 5. Deploy with Helm

```bash
cd helm/simple-crud-app

helm install crud-app . \
  -f values.yaml -f values-monitoring.yaml \
  -n crud --create-namespace \
  --set image.pullPolicy=Never \
  --set cnpg.instances=1 \
  --set service.type=NodePort
```

> - `values-monitoring.yaml` enables ServiceMonitor, CNPG PodMonitor, and Grafana dashboard
> - `image.pullPolicy=Never` — use the locally built image
> - `cnpg.instances=1` — single PostgreSQL instance (sufficient for minikube)
> - `service.type=NodePort` — expose the service for `minikube service` access

### 6. Verify the Deployment

```bash
# Check CNPG cluster is ready
kubectl get cluster -n crud -w

# Check all pods are running
kubectl get pods -n crud

# Verify ServiceMonitor is created
kubectl get servicemonitor -n crud

# Check the CNPG-generated secret exists
kubectl get secret -n crud | grep pg-app

# Wait for the app deployment to be ready
kubectl wait --for=condition=Available deployment/crud-app-simple-crud-app \
  -n crud --timeout=180s
```

### 7. Access the API

**Option A — minikube service (recommended for minikube):**

```bash
minikube service crud-app-simple-crud-app -n crud
```

**Option B — kubectl port-forward:**

```bash
kubectl port-forward svc/crud-app-simple-crud-app 8000:80 -n crud
```

Then open http://localhost:8000/docs

### 8. Access Grafana

**Option A — minikube service (since Grafana is NodePort):**

```bash
minikube service prometheus-stack-grafana -n monitoring
```

**Option B — kubectl port-forward:**

```bash
kubectl port-forward svc/prometheus-stack-grafana 3000:80 -n monitoring
```

Open http://localhost:3000
- **Username:** `admin`
- **Password:** `admin123`

> Forgot the password? Retrieve it:
> ```bash
> kubectl get secret prometheus-stack-grafana -n monitoring \
>   -o jsonpath="{.data.admin-password}" | base64 -d
> ```

The **Loki datasource** is auto-provisioned via the `loki-datasource` ConfigMap.
The **FastAPI CRUD App** dashboard is auto-provisioned and shows:
- Request rate and latency (p95)
- Active requests and 5xx error rate
- Application logs (via Loki)
- CNPG transactions per second and replication lag

**Import additional dashboards** — Go to Dashboards → Import → Enter ID:

| Dashboard             | Grafana ID |
|-----------------------|------------|
| Kubernetes Cluster    | 315        |
| Node Exporter         | 1860       |
| Loki Logs             | 13639      |
| Pod Logs              | 15141      |

**Access Prometheus UI:**

```bash
kubectl port-forward svc/prometheus-stack-kube-prom-prometheus 9090:9090 -n monitoring
```

Open http://localhost:9090

### 9. Test It

```bash
# Replace <URL> with the minikube service URL or http://localhost:8000

# Create an item
curl -X POST <URL>/api/v1/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "description": "A test widget", "price": 9.99}'

# List items
curl <URL>/api/v1/items/

# Health check
curl <URL>/health
```

### Troubleshooting

| Issue | Fix |
|-------|-----|
| Pods in Pending | Increase Minikube memory: `minikube start --memory=6144` |
| Loki not showing in Grafana | Verify datasource ConfigMap: `kubectl get cm -n monitoring \| grep loki` |
| No metrics from app | Check ServiceMonitor labels match: `kubectl get servicemonitor -n crud -o yaml` |
| Grafana password forgot | `kubectl get secret prometheus-stack-grafana -n monitoring -o jsonpath="{.data.admin-password}" \| base64 -d` |

```bash
# CNPG cluster not becoming healthy
kubectl describe cluster crud-app-simple-crud-app-pg -n crud
kubectl logs -l cnpg.io/cluster=crud-app-simple-crud-app-pg -n crud

# App pod stuck in init (waiting for PG)
kubectl logs <pod-name> -c wait-for-pg -n crud

# App pod crash loop
kubectl logs <pod-name> -n crud

# Check the DATABASE_URL being used
kubectl exec <pod-name> -n crud -- env | grep DATABASE_URL
```

### Cleanup

```bash
helm uninstall crud-app -n crud
helm uninstall loki -n monitoring
helm uninstall prometheus-stack -n monitoring
kubectl delete namespace crud monitoring
minikube stop
```

## Helm Deployment (General)

**Prerequisite:** Install the [CloudNativePG operator](https://cloudnative-pg.io/) in your cluster first:

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.25/releases/cnpg-1.25.0.yaml
```

Then deploy:

```bash
cd helm/simple-crud-app
helm install crud-app . -n crud --create-namespace
```

Override values:

```bash
helm install crud-app . \
  -n crud --create-namespace \
  --set image.repository=myregistry/simple-crud-app \
  --set image.tag=v0.1.0 \
  --set ingress.enabled=true \
  --set cnpg.instances=3
```