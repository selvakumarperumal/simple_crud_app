# simple-crud-app / values.yaml — Documentation

**File:** [values.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/values.yaml)

---

## What is values.yaml?

The default configuration for the chart. Every key here is accessible in templates via `{{ .Values.<key> }}`. Users override values with `--set` or `-f custom-values.yaml`.

---

## Line-by-Line Explanation

```yaml
# Line 1
replicaCount: 4
```

- Number of pod replicas for the Deployment.
- **Ignored when HPA is enabled** — the `deployment.yaml` template has `{{- if not .Values.autoscaling.enabled }}` around the `replicas:` field.
- `4` provides redundancy and high availability.

---

```yaml
# Lines 2 (blank)
```

---

```yaml
# Lines 3-6
image:
  repository: simple-crud-app
  tag: latest
  pullPolicy: Always
```

- **`repository: simple-crud-app`** — Docker image name. For ECR, override to `<account-id>.dkr.ecr.<region>.amazonaws.com/simple-crud-app`.
- **`tag: latest`** — Image tag. In production, use a specific version (e.g., `v0.1.0`) to avoid deploying unexpected changes.
- **`pullPolicy: Always`** — Kubernetes will always pull the image, ensuring that the latest changes are deployed.
  - `Always` — Always pull (good for `latest` tag in production).
  - `Never` — Never pull (required for Minikube with local images).
  - `IfNotPresent` — Pull only if missing (default, good balance).

Used in `deployment.yaml`:
```yaml
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
imagePullPolicy: {{ .Values.image.pullPolicy }}
```

---

```yaml
# Lines 7 (blank)
```

---

```yaml
# Lines 8-11
service:
  type: ClusterIP
  port: 80
  targetPort: 8000
```

- **`type: ClusterIP`** — Service is only accessible within the cluster. Options:
  - `ClusterIP` — Internal only (default). Use with Ingress or port-forward for external access.
  - `NodePort` — Exposes on each node's IP at a static port. Good for Minikube.
  - `LoadBalancer` — Provisions an external cloud load balancer (AWS NLB/ALB, GCP LB).

- **`port: 80`** — The port the Service listens on. Clients connect to `<service-name>:80`.
- **`targetPort: 8000`** — The port on the container the Service forwards traffic to. Uvicorn listens on 8000.

**Traffic flow:** `Client → Service:80 → Pod:8000 → uvicorn`

---

```yaml
# Lines 12 (blank)
```

---

```yaml
# Lines 13-20
istio:
  enabled: true
  gateway:
    create: true
    selector:
      istio: ingressgateway
  hosts:
    - crud-app.local
```

- **`enabled: true`** — Creates Istio VirtualService (and optionally Gateway) for routing external HTTP traffic. Replaces standard Kubernetes Ingress.
- **`gateway.create: true`** — Creates an Istio `Gateway` resource for the app. If false, you can specify `gateway.name` to attach the VirtualService to an existing shared Gateway.
- **`gateway.selector`** — Pod labels used to select the Istio ingress gateway deployment (default: `istio: ingressgateway`).
- **`hosts`** — List of hostnames to route.
  - `crud-app.local` — The domain name. The VirtualService will route traffic matching this host to the application.

---

```yaml
# Lines 22 (blank)
```

---

```yaml
# Lines 23-29
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi
```

- **`requests`** — Minimum guaranteed resources (used for pod scheduling):
  - `cpu: 100m` — 0.1 CPU cores (100 millicores).
  - `memory: 128Mi` — 128 MiB RAM.
- **`limits`** — Maximum allowed resources:
  - `cpu: 500m` — 0.5 CPU cores. Pod is CPU-throttled beyond this.
  - `memory: 256Mi` — Pod is OOM-killed if it exceeds this.
- **QoS class:** Since requests ≠ limits, the pod gets `Burstable` QoS. It normally uses minimal resources but can burst during traffic spikes.

Injected in `deployment.yaml` via `{{ toYaml .Values.resources | nindent 12 }}`.

---

```yaml
# Lines 30 (blank)
```

---

```yaml
# Lines 31-35
autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 80
```

- **`enabled: false`** — HPA (HorizontalPodAutoscaler) is NOT created by default.
- **`minReplicas: 2`** — Never scale below 2 pods (maintains redundancy).
- **`maxReplicas: 5`** — Never scale above 5 pods (cost control).
- **`targetCPUUtilizationPercentage: 80`** — Scale up when average CPU across pods exceeds 80% of the requested CPU (100m). So if pods are averaging >80m CPU, Kubernetes adds more pods.

When `enabled: true`:
1. The `replicas:` field is omitted from the Deployment (HPA controls it).
2. The `hpa.yaml` template renders a HorizontalPodAutoscaler resource.

---

```yaml
# Lines 36 (blank)
```

---

```yaml
# Lines 37-41
database:
  secretName: crud-db-app
  secretKey: uri
  host: crud-db-rw
  port: 5432
```

- **This connects the app to the CNPG database.** All four values come from what CNPG auto-creates.
- **`secretName: crud-db-app`** — The Kubernetes Secret that CNPG created (named `<cluster-name>-<owner>`). Contains the full PostgreSQL connection URI.
- **`secretKey: uri`** — The key inside the Secret that holds the connection string. Value looks like: `postgresql://app:<password>@crud-db-rw:5432/crud_db`.
- **`host: crud-db-rw`** — The CNPG read-write Service name. Used by the init container (`wait-for-pg`) to check if PostgreSQL is reachable before starting the app.
- **`port: 5432`** — PostgreSQL default port. Used by the init container's `nc -z` (netcat) connectivity check.

> [!IMPORTANT]
> If you change `cluster.name` in the cnpg-cluster chart, you must also update `secretName` and `host` here to match the new names.

---

```yaml
# Lines 42 (blank)
```

---

```yaml
# Lines 43-52
monitoring:
  serviceMonitor:
    enabled: true
    interval: 15s
    additionalLabels:
      release: prometheus-stack
  grafana:
    dashboards:
      enabled: true
```

- **`serviceMonitor.enabled: true`** — Creates a `ServiceMonitor` CRD so Prometheus scrapes `/metrics` from the app.
- **`serviceMonitor.interval: 15s`** — Prometheus scrapes every 15 seconds.
- **`serviceMonitor.additionalLabels`** — Extra labels to add to the ServiceMonitor. Set to `release: prometheus-stack` so the Prometheus operator discovers it.
- **`grafana.dashboards.enabled: true`** — Creates a ConfigMap with the Grafana dashboard JSON. Grafana's sidecar auto-imports it.
