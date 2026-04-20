# simple-crud-app / templates/servicemonitor.yaml — Documentation

**File:** [servicemonitor.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/servicemonitor.yaml)

---

## What Does This File Create?

A **ServiceMonitor** — a Prometheus Operator custom resource that tells Prometheus how and where to scrape metrics from the FastAPI application. Only created when `monitoring.serviceMonitor.enabled: true`.

---

## Line-by-Line Explanation

```yaml
# Line 1
{{- if .Values.monitoring.serviceMonitor.enabled }}
```

- **Guard** — Only rendered when `monitoring.serviceMonitor.enabled` is `true`. Default is `false`. Enabled via `values-monitoring.yaml` overlay.

---

```yaml
# Lines 2-3
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
```

- **`monitoring.coreos.com/v1`** — API group registered by the Prometheus Operator CRD. This resource only works when the Prometheus Operator is installed (e.g., via kube-prometheus-stack).
- **`ServiceMonitor`** — Tells the Prometheus Operator to configure Prometheus to scrape a specific Service's pods.

---

```yaml
# Lines 4-10
metadata:
  name: {{ include "simple-crud-app.fullname" . }}
  labels:
    {{- include "simple-crud-app.labels" . | nindent 4 }}
    {{- with .Values.monitoring.serviceMonitor.additionalLabels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
```

- **`name`** — Same fullname as other resources.
- **`labels`** — Full chart labels PLUS additional labels from values.yaml.
- **`{{- with .Values.monitoring.serviceMonitor.additionalLabels }}`** — The `with` block changes the context (`.`) to `additionalLabels`. If `additionalLabels` is empty/nil, the block is skipped entirely.
- **`{{- toYaml . | nindent 4 }}`** — Converts `additionalLabels` to YAML. When using `values-monitoring.yaml`, this outputs: `release: prometheus-stack`.
- **Why `additionalLabels` matters:** The Prometheus Operator's `serviceMonitorSelector` filters which ServiceMonitors to process. kube-prometheus-stack typically requires `release: <release-name>`. Without this label, Prometheus **ignores** the ServiceMonitor.

---

```yaml
# Lines 11-14
spec:
  selector:
    matchLabels:
      {{- include "simple-crud-app.selectorLabels" . | nindent 6 }}
```

- **`spec.selector.matchLabels`** — Tells the ServiceMonitor which **Service** to target.
- Uses selectorLabels: `app.kubernetes.io/name: simple-crud-app` + `app.kubernetes.io/instance: crud-app`.
- The ServiceMonitor finds the Service with these labels, then discovers the pods behind it.

---

```yaml
# Lines 15-18
  endpoints:
    - port: http
      path: /metrics
      interval: {{ .Values.monitoring.serviceMonitor.interval }}
```

- **`endpoints`** — Defines how to scrape each pod.
- **`port: http`** — Scrape the port named `http` on the Service (which maps to container port 8000). This matches the named port in `service.yaml`.
- **`path: /metrics`** — The HTTP path to scrape. The FastAPI app exposes Prometheus metrics at this endpoint (configured in `app/main.py`).
- **`interval: 15s`** — Prometheus scrapes every 15 seconds.

**Complete scrape flow:**
```
Prometheus Operator reads ServiceMonitor
  → finds Service matching selector labels
    → discovers Pod IPs behind the Service
      → scrapes GET http://<pod-ip>:8000/metrics every 15s
```

---

```yaml
# Line 19
{{- end }}
```

- Closes the `if` guard.

---

## Metrics Exposed by the App

The FastAPI app at `/metrics` exposes (via `prometheus_client`):

| Metric | Type | Description |
|--------|------|-------------|
| `http_request_duration_seconds` | Histogram | Request latency (buckets + count + sum) |
| `http_requests_in_progress` | Gauge | Currently in-flight requests |

These are the metrics queried by the Grafana dashboard panels.
