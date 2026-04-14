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
- **ArgoCD** — GitOps continuous delivery

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
├── cnpg-cluster/           # Helm chart for PostgreSQL (CNPG)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── _helpers.tpl
│       └── cluster.yaml
└── simple-crud-app/        # Helm chart for the FastAPI app
    ├── Chart.yaml
    ├── values.yaml
    ├── values-monitoring.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        ├── hpa.yaml
        ├── servicemonitor.yaml
        ├── loki-datasource.yaml
        └── grafana-dashboard.yaml
argocd/
├── app-of-apps.yaml              # Root Application (bootstrap)
└── apps/
    ├── cnpg-operator.yaml         # Wave 0 — CNPG operator
    ├── monitoring-stack.yaml      # Wave 0 — Prometheus + Grafana
    ├── loki.yaml                  # Wave 1 — Loki + Promtail
    ├── cnpg-cluster.yaml          # Wave 2 — PostgreSQL cluster
    └── crud-app.yaml              # Wave 3 — FastAPI application
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
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo update

helm install cnpg cnpg/cloudnative-pg \
  --namespace cnpg-system --create-namespace

kubectl wait --for=condition=Available deployment/cnpg-cloudnative-pg \
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

### 5. Deploy the Database (CNPG Cluster)

```bash
helm install crud-db helm/cnpg-cluster \
  -n crud --create-namespace \
  --set cluster.instances=1

# Wait for the cluster to be ready
kubectl get cluster -n crud -w
```

> `cluster.instances=1` — single PostgreSQL instance (sufficient for minikube)
>
> CNPG creates a secret `crud-db-app` with the connection URI and a service `crud-db-rw` for read-write access.

### 6. Deploy the App with Helm

```bash
helm install crud-app helm/simple-crud-app \
  -f helm/simple-crud-app/values.yaml \
  -f helm/simple-crud-app/values-monitoring.yaml \
  -n crud \
  --set image.pullPolicy=Never \
  --set service.type=NodePort
```

> - `values-monitoring.yaml` enables ServiceMonitor and Grafana dashboard
> - `image.pullPolicy=Never` — use the locally built image
> - `service.type=NodePort` — expose the service for `minikube service` access

### 7. Verify the Deployment

```bash
# Check CNPG cluster is ready
kubectl get cluster -n crud

# Check all pods are running
kubectl get pods -n crud

# Verify ServiceMonitor is created
kubectl get servicemonitor -n crud

# Check the CNPG-generated secret exists
kubectl get secret -n crud | grep crud-db-app

# Wait for the app deployment to be ready
kubectl wait --for=condition=Available deployment/crud-app-simple-crud-app \
  -n crud --timeout=180s
```

### 8. Access the API

**Option A — minikube service (recommended for minikube):**

```bash
minikube service crud-app-simple-crud-app -n crud
```

**Option B — kubectl port-forward:**

```bash
kubectl port-forward svc/crud-app-simple-crud-app 8000:80 -n crud
```

Then open http://localhost:8000/docs

### 9. Access Grafana

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

### 10. Access Prometheus UI:

```bash
kubectl port-forward svc/prometheus-stack-kube-prom-prometheus 9090:9090 -n monitoring
```

Open http://localhost:9090

### 11. Test It

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
kubectl describe cluster crud-db -n crud
kubectl logs -l cnpg.io/cluster=crud-db -n crud

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
helm uninstall crud-db -n crud
helm uninstall loki -n monitoring
helm uninstall prometheus-stack -n monitoring
helm uninstall cnpg -n cnpg-system
kubectl delete namespace crud monitoring cnpg-system
minikube stop
```

## Deploy with ArgoCD (GitOps)

ArgoCD manages the full stack declaratively — no manual `helm install` or `kubectl wait` needed. Sync waves ensure correct ordering:

| Wave | Application | What it deploys |
|------|-------------|------------------|
| 0 | `cnpg-operator` | CloudNativePG operator |
| 0 | `monitoring-stack` | Prometheus + Grafana (kube-prometheus-stack) |
| 1 | `loki` | Loki + Promtail |
| 2 | `cnpg-cluster` | PostgreSQL cluster (CNPG) |
| 3 | `crud-app` | FastAPI application |

ArgoCD waits for each wave's resources to be **healthy** before proceeding — it natively understands Deployment readiness, CNPG Cluster health, StatefulSet availability, etc. This replaces all `kubectl wait` commands.

### 1. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=Available deployment/argocd-server \
  -n argocd --timeout=120s
```

### 2. Update Git Repo URL

Edit the `repoURL` in these files to point to your Git repository:

- `argocd/app-of-apps.yaml`
- `argocd/apps/cnpg-cluster.yaml`
- `argocd/apps/crud-app.yaml`

```bash
# Example: replace placeholder with your actual repo
sed -i 's|https://github.com/<your-org>/simple_crud_app.git|https://github.com/myuser/simple_crud_app.git|g' \
  argocd/app-of-apps.yaml argocd/apps/cnpg-cluster.yaml argocd/apps/crud-app.yaml
```

### 3. Build the Docker Image (Minikube only)

```bash
eval $(minikube docker-env)
docker build -t simple-crud-app:latest .
```

### 4. Bootstrap — Apply the App-of-Apps

```bash
kubectl apply -f argocd/app-of-apps.yaml
```

This single command deploys **everything**. ArgoCD will:
1. Install CNPG operator + monitoring stack (wave 0)
2. Install Loki (wave 1)
3. Create the PostgreSQL cluster (wave 2)
4. Deploy the FastAPI app (wave 3)

### 5. Access ArgoCD UI

```bash
# Get the admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo

# Port-forward the ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open https://localhost:8080
- **Username:** `admin`
- **Password:** (from the command above)

### 6. Verify All Applications

```bash
# Install ArgoCD CLI (optional)
# brew install argocd  OR  curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64 && chmod +x argocd

# Check all app statuses
kubectl get applications -n argocd

# Expected output — all should be Synced/Healthy:
# NAME               SYNC STATUS   HEALTH STATUS
# cnpg-operator      Synced        Healthy
# monitoring-stack   Synced        Healthy
# loki               Synced        Healthy
# cnpg-cluster       Synced        Healthy
# crud-app           Synced        Healthy
```

### ArgoCD Cleanup

```bash
kubectl delete -f argocd/app-of-apps.yaml
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl delete namespace argocd
```

## Helm Deployment (Manual — without ArgoCD)

**Prerequisite:** Install the [CloudNativePG operator](https://cloudnative-pg.io/) in your cluster first:

```bash
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm install cnpg cnpg/cloudnative-pg \
  --namespace cnpg-system --create-namespace
```

Then deploy:

```bash
# Deploy the database
helm install crud-db helm/cnpg-cluster -n crud --create-namespace

# Deploy the app
helm install crud-app helm/simple-crud-app -n crud
```

Override values:

```bash
helm install crud-db helm/cnpg-cluster -n crud --create-namespace \
  --set cluster.instances=3

helm install crud-app helm/simple-crud-app -n crud \
  --set image.repository=myregistry/simple-crud-app \
  --set image.tag=v0.1.0 \
  --set ingress.enabled=true
```