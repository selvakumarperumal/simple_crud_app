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
- **Terraform** *(optional)* — infrastructure provisioning (EKS, IAM, IRSA)

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
- [helm](https://helm.sh/docs/intro/install/) *(Option B only — ArgoCD has a built-in Helm renderer)*

### 1. Start Minikube

```bash
minikube start --cpus 4 --memory 4096 --driver=docker
```

### 2. Build the Docker Image

```bash
minikube image build -t simple-crud-app:latest .
```

> **Alternative:** If you prefer using the Docker CLI directly:
> ```bash
> eval $(minikube docker-env)
> docker build -t simple-crud-app:latest .
> ```

Now choose **one** of the two deployment methods below:

---

## Option A: Deploy with ArgoCD (Recommended)

ArgoCD manages the full stack declaratively — **no manual `helm install` or `kubectl wait` needed**. Sync waves ensure correct ordering:

| Wave | Application | What it deploys |
|------|-------------|------------------|
| 0 | `cnpg-operator` | CloudNativePG operator |
| 0 | `monitoring-stack` | Prometheus + Grafana (kube-prometheus-stack) |
| 1 | `loki` | Loki + Promtail |
| 2 | `cnpg-cluster` | PostgreSQL cluster (CNPG) |
| 3 | `crud-app` | FastAPI application |

ArgoCD waits for each wave's resources to be **healthy** before proceeding — it natively understands Deployment readiness, CNPG Cluster health, StatefulSet availability, etc.

### A1. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=Available deployment/argocd-server \
  -n argocd --timeout=120s
```

### A2. Update Git Repo URL

Edit the `repoURL` in these files to point to your Git repository:

- `argocd/app-of-apps.yaml`
- `argocd/apps/cnpg-cluster.yaml`
- `argocd/apps/crud-app.yaml`

```bash
# Example: replace placeholder with your actual repo
sed -i 's|https://github.com/<your-org>/simple_crud_app.git|https://github.com/myuser/simple_crud_app.git|g' \
  argocd/app-of-apps.yaml argocd/apps/cnpg-cluster.yaml argocd/apps/crud-app.yaml
```

### A3. Bootstrap — Apply the App-of-Apps

```bash
kubectl apply -f argocd/app-of-apps.yaml
```

This single command deploys **everything**. ArgoCD will:
1. Install CNPG operator + monitoring stack (wave 0)
2. Install Loki (wave 1)
3. Create the PostgreSQL cluster (wave 2)
4. Deploy the FastAPI app (wave 3)

### A4. Access ArgoCD UI

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

### A5. Verify All Applications

```bash
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

### A6. ArgoCD Cleanup

```bash
kubectl delete -f argocd/app-of-apps.yaml
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl delete namespace argocd cnpg-system monitoring crud
minikube stop
```

---

## Option B: Deploy Manually (Helm)

Use this if you prefer manual control without ArgoCD.

### B1. Install CloudNativePG Operator

```bash
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo update

helm install cnpg cnpg/cloudnative-pg \
  --namespace cnpg-system --create-namespace

kubectl wait --for=condition=Available deployment/cnpg-cloudnative-pg \
  -n cnpg-system --timeout=120s
```

### B2. Install Monitoring Stack (Prometheus + Grafana + Loki)

```bash
# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (Prometheus + Grafana)
helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
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

### B3. Deploy the Database (CNPG Cluster)

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

### B4. Deploy the App

```bash
helm install crud-app helm/simple-crud-app \
  -f helm/simple-crud-app/values.yaml \
  -f helm/simple-crud-app/values-monitoring.yaml \
  -n crud \
  --set image.pullPolicy=Never \
  --set service.type=NodePort
```

### B5. Verify the Deployment

```bash
kubectl get cluster -n crud
kubectl get pods -n crud
kubectl get servicemonitor -n crud
kubectl get secret -n crud | grep crud-db-app

kubectl wait --for=condition=Available deployment/crud-app-simple-crud-app \
  -n crud --timeout=180s
```

### B6. Manual Cleanup

```bash
helm uninstall crud-app -n crud
helm uninstall crud-db -n crud
helm uninstall loki -n monitoring
helm uninstall prometheus-stack -n monitoring
helm uninstall cnpg -n cnpg-system
kubectl delete namespace crud monitoring cnpg-system
minikube stop
```

---

## Access the Services

### Access the API

**Option A — minikube service (recommended for minikube):**

```bash
minikube service crud-app-simple-crud-app -n crud
```

**Option B — kubectl port-forward:**

```bash
kubectl port-forward svc/crud-app-simple-crud-app 8000:80 -n crud
```

Then open http://localhost:8000/docs

### Access Grafana

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

### Access Prometheus UI

```bash
kubectl port-forward svc/prometheus-stack-kube-prom-prometheus 9090:9090 -n monitoring
```

Open http://localhost:9090

### Test the API

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

## Troubleshooting

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

## Deploy on EKS

### Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured (`aws configure`)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [eksctl](https://eksctl.io/) *(or an existing EKS cluster)*

### 1. Create the EKS Cluster (if needed)

```bash
eksctl create cluster \
  --name crud-cluster \
  --region ap-south-1 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 2 \
  --managed

# Verify
kubectl get nodes
```

### 2. Install the EBS CSI Driver (for CNPG storage)

```bash
# Create IAM OIDC provider (if not already)
eksctl utils associate-iam-oidc-provider --cluster crud-cluster --approve

# Install the EBS CSI addon
eksctl create addon --name aws-ebs-csi-driver --cluster crud-cluster --force
```

### 3. Create ECR Repository and Push the Image

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=ap-south-1

# Create ECR repository
aws ecr create-repository --repository-name simple-crud-app --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push
docker build -t simple-crud-app:latest .
docker tag simple-crud-app:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/simple-crud-app:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/simple-crud-app:latest
```

### 4. Deploy with ArgoCD (Recommended)

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=120s

# Update repoURL in argocd/ files (see Option A step A2)

# Update image in argocd/apps/crud-app.yaml valuesObject:
#   image:
#     repository: <account-id>.dkr.ecr.<region>.amazonaws.com/simple-crud-app
#     tag: latest
#     pullPolicy: Always

# Bootstrap
kubectl apply -f argocd/app-of-apps.yaml
```

> On EKS, remove `image.pullPolicy: Never` and `service.type: NodePort` from the `crud-app.yaml` ArgoCD Application — those are minikube-only settings.

### 5. Access the Services

```bash
# ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# API
kubectl port-forward svc/crud-app-simple-crud-app 8000:80 -n crud

# Grafana
kubectl port-forward svc/prometheus-stack-grafana 3000:80 -n monitoring
```

Or enable Ingress for external access:

```bash
# Option: AWS ALB Ingress Controller
# Install: https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html

# Then set in values:
#   ingress.enabled=true
#   ingress.className=alb
```

### EKS Cleanup

```bash
kubectl delete -f argocd/app-of-apps.yaml
kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
eksctl delete cluster --name crud-cluster --region ap-south-1
```

### Key Differences: Minikube vs EKS

| | Minikube | EKS |
|---|---|---|
| **Image** | `minikube docker-env` + local build | ECR push |
| **pullPolicy** | `Never` | `Always` (or `IfNotPresent`) |
| **Service access** | `minikube service` / NodePort | `port-forward` / LoadBalancer / ALB Ingress |
| **CNPG storage** | Default (hostpath) | EBS via CSI driver (`gp3`) |
| **Helm CLI** | Not needed with ArgoCD | Not needed with ArgoCD |

## Terraform + ArgoCD Architecture (Production Pattern)

In production, split responsibilities between **Terraform** (infrastructure) and **ArgoCD** (applications):

### What goes where

| Tool | Scope | Examples |
|---|---|---|
| **Terraform** | AWS infrastructure that rarely changes | EKS cluster, VPC, subnets, security groups, IAM roles, OIDC provider, IRSA service accounts, EBS CSI addon |
| **ArgoCD** | Kubernetes workloads that change often | CNPG, Prometheus, Grafana, Loki, Istio, Cluster Autoscaler, your app |

> **Why not Terraform `helm_release` for everything?** Terraform manages state externally — it has no auto-sync, no self-heal, and no drift detection for K8s resources. ArgoCD continuously reconciles the cluster state with Git.

### IRSA pattern (Cluster Autoscaler, ALB Controller, External DNS, etc.)

AWS workloads that need IAM permissions require an **IRSA** (IAM Role for Service Account). ArgoCD can't create IAM resources, so split it:

**Step 1 — Terraform/eksctl creates the IAM role + Kubernetes ServiceAccount:**

```bash
exsctl create iamserviceaccount \
  --cluster crud-cluster \
  --name cluster-autoscaler \
  --namespace kube-system \
  --attach-policy-arn arn:aws:iam::<account>:policy/ClusterAutoscalerPolicy \
  --approve
```

**Step 2 — ArgoCD deploys the Helm chart, using the existing ServiceAccount:**

```yaml
# argocd/apps/cluster-autoscaler.yaml
helm:
  valuesObject:
    rbac:
      serviceAccount:
        create: false                   # Don't create — IRSA already made it
        name: cluster-autoscaler        # Use the one from step 1
    autoDiscovery:
      clusterName: crud-cluster
```

This same pattern applies to **any** IRSA-dependent workload:

| Workload | IAM Role (Terraform/eksctl) | Helm Chart (ArgoCD) |
|---|---|---|
| Cluster Autoscaler | `ClusterAutoscalerPolicy` | `autoscaler/cluster-autoscaler` |
| ALB Ingress Controller | `AWSLoadBalancerControllerPolicy` | `eks/aws-load-balancer-controller` |
| External DNS | `ExternalDNSPolicy` | `external-dns/external-dns` |
| EBS CSI Driver | EKS addon (managed by `eksctl`/Terraform) | — |

### Istio with ArgoCD

Istio is a pure Kubernetes workload — no IAM needed. Deploy it with ArgoCD using sync waves:

| Component | Chart | Sync Wave |
|---|---|---|
| `istio-base` | `istio/base` (CRDs) | Wave 0 |
| `istiod` | `istio/istiod` (control plane) | Wave 1 |
| `istio-gateway` | `istio/gateway` (ingress) | Wave 2 |

ArgoCD waits for CRDs (wave 0) before deploying istiod (wave 1), then the gateway (wave 2).

> **Exception:** If the Istio ingress gateway needs an AWS NLB, the gateway's ServiceAccount may need IRSA — use the same pattern above (Terraform creates IAM role, ArgoCD deploys the chart with `serviceAccount.create: false`).

### Summary flow

```
Terraform apply
  └── EKS cluster + VPC + IAM roles + IRSA service accounts
        └── ArgoCD (installed via kubectl apply)
              └── app-of-apps.yaml
                    ├── Wave 0: CNPG operator, Prometheus+Grafana, Istio base
                    ├── Wave 1: Loki, istiod
                    ├── Wave 2: CNPG cluster, Istio gateway
                    └── Wave 3: Your application
```

## Helm Deployment (General — Non-Minikube)

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