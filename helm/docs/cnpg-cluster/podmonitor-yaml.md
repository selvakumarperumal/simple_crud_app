# cnpg-cluster / templates/podmonitor.yaml — Documentation

**File:** [podmonitor.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/cnpg-cluster/templates/podmonitor.yaml)

---

## What Does This File Create?

A **`PodMonitor`** custom resource. This resource is defined by the Prometheus Operator. It tells Prometheus how to scrape metrics directly from the PostgreSQL pods created by the CloudNativePG operator.

---

## Line-by-Line Explanation

```yaml
# Line 1
{{- if .Values.cluster.monitoring.enabled }}
```

- **Conditional block** — Only creates the PodMonitor if `monitoring.enabled` is `true` in `values.yaml`.

---

```yaml
# Lines 2-5
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: {{ include "cnpg-cluster.name" . }}
```

- **`apiVersion: monitoring.coreos.com/v1`** — This is a custom API provided by the Prometheus Operator. If Prometheus Operator is not installed, applying this file will result in an error (`no matches for kind "PodMonitor"`).
- **`name`** — Typically `crud-db` (matches the cluster name).

---

```yaml
# Lines 6-10
  labels:
    {{- include "cnpg-cluster.labels" . | nindent 4 }}
    {{- with .Values.cluster.monitoring.additionalLabels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
```

- **Standard Labels** — Injected via the helper template.
- **`additionalLabels`** — Crucial for Prometheus auto-discovery! Prometheus operators usually look for PodMonitors matching a specific label (like `release: prometheus-stack`). By injecting these labels, the operator knows it should pick up this monitor.

---

```yaml
# Lines 11-14
spec:
  namespaceSelector:
    matchNames:
      - {{ .Release.Namespace }}
```

- **`namespaceSelector`** — Tells Prometheus to only look for matching pods in the release's namespace (e.g., `crud`). This prevents Prometheus from accidentally monitoring pods with the same labels in other namespaces.

---

```yaml
# Lines 15-18
  selector:
    matchLabels:
      cnpg.io/cluster: {{ include "cnpg-cluster.name" . }}
      cnpg.io/podRole: instance
```

- **`selector`** — Tells Prometheus *which* pods to scrape.
- **`cnpg.io/cluster: crud-db`** — Only select pods belonging to this specific CNPG cluster.
- **`cnpg.io/podRole: instance`** — Ensures we only select the actual PostgreSQL instance pods, ignoring auxiliary pods (like backups or initialization pods).

---

```yaml
# Lines 19-21
  podMetricsEndpoints:
    - port: metrics
      interval: {{ .Values.cluster.monitoring.interval }}
```

- **`podMetricsEndpoints`** — How to scrape the pods.
- **`port: metrics`** — The named port exposed by the CNPG instances. The CNPG operator automatically configures its pods to expose Prometheus metrics on port `9187` under the name `metrics`.
- **`interval`** — How often to scrape (e.g., `15s`). Defined in `values.yaml`.

---

```yaml
# Line 22
{{- end }}
```

- **End of conditional block**.
