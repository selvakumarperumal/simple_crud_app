# simple-crud-app / values-monitoring.yaml — Documentation

**File:** [values-monitoring.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/values-monitoring.yaml)

---

## What is a Values Overlay File?

A values overlay file overrides specific keys from the base `values.yaml`. When you pass multiple `-f` flags to Helm, they are **deep-merged** in order — later files override earlier ones.

```bash
# Usage:
helm install crud-app . -f values.yaml -f values-monitoring.yaml
```

Only the `monitoring:` section is overridden. All other keys (`replicaCount`, `image`, `service`, etc.) come from the base `values.yaml` unchanged.

---

## Line-by-Line Explanation

```yaml
# Line 1
# values-monitoring.yaml
```

- Comment identifying the file.

---

```yaml
# Line 2
# Overlay to enable full monitoring stack integration.
```

- Comment explaining the file's purpose.

---

```yaml
# Line 3
# Usage: helm install crud-app . -f values.yaml -f values-monitoring.yaml
```

- Comment showing the exact command. The order matters: `-f values.yaml` is the base, `-f values-monitoring.yaml` overrides it.

---

```yaml
# Lines 4 (blank)
```

---

```yaml
# Lines 5-7
monitoring:
  serviceMonitor:
    enabled: true
```

- **Overrides** `monitoring.serviceMonitor.enabled` from `false` → `true`.
- **Effect:** The `servicemonitor.yaml` template is now rendered, creating a `ServiceMonitor` CRD.

---

```yaml
# Line 8
    interval: 15s
```

- Prometheus scrapes the app's `/metrics` endpoint every 15 seconds.
- Same as the default — included here for explicitness.

---

```yaml
# Lines 9-10
    additionalLabels:
      release: prometheus-stack
```

- **Critical for Prometheus discovery.** The Prometheus Operator only scrapes ServiceMonitors that match its `serviceMonitorSelector`. The kube-prometheus-stack Helm chart configures this selector to filter on `release: <release-name>`.
- If you installed kube-prometheus-stack with `helm install prometheus-stack ...`, the release name is `prometheus-stack`, so this label must match.
- **Without this label**, Prometheus ignores the ServiceMonitor and the app's metrics are never collected — the Grafana dashboard panels would show "No data."

---

```yaml
# Lines 11-13
  grafana:
    dashboards:
      enabled: true
```

- **Overrides** `monitoring.grafana.dashboards.enabled` from `false` → `true`.
- **Effect:** The `grafana-dashboard.yaml` template renders, creating a ConfigMap with `grafana_dashboard: "1"` label. The Grafana sidecar auto-imports it.

---

```yaml
# Lines 14-18
  loki:
    datasource:
      enabled: true
      url: http://loki:3100
      grafanaNamespace: monitoring
```

- **`enabled: true`** — Overrides to `true`. Creates the Loki datasource ConfigMap.
- **`url: http://loki:3100`** — The in-cluster URL for the Loki service. `loki` is the Kubernetes Service name created by the loki-stack Helm chart in the monitoring namespace. Port `3100` is Loki's default HTTP port.
- **`grafanaNamespace: monitoring`** — The ConfigMap is created in THIS namespace (where Grafana runs), not in the app's namespace. The Grafana sidecar only watches ConfigMaps in its own namespace by default.

---

## Why a Separate File?

This design pattern provides **environment-specific configuration**:

```bash
# Development — no monitoring
helm install crud-app . -f values.yaml

# Production — full monitoring
helm install crud-app . -f values.yaml -f values-monitoring.yaml

# You could also create other overlays:
#   values-production.yaml  (more replicas, larger resources)
#   values-staging.yaml     (different image tag)
```

This avoids duplicating the entire `values.yaml` for different environments.
