# simple-crud-app / templates/loki-datasource.yaml — Documentation

**File:** [loki-datasource.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/loki-datasource.yaml)

---

## What Does This File Create?

A Kubernetes **ConfigMap** that auto-provisions Loki as a datasource in Grafana. The Grafana sidecar container detects ConfigMaps with the label `grafana_datasource: "1"` and loads the datasource configuration automatically. Only created when `monitoring.loki.datasource.enabled: true`.

---

## Line-by-Line Explanation

```yaml
# Line 1
{{- if .Values.monitoring.loki.datasource.enabled }}
```

- **Guard** — Only rendered when `monitoring.loki.datasource.enabled` is `true`. Default is `false`.

---

```yaml
# Lines 2-3
apiVersion: v1
kind: ConfigMap
```

- Standard Kubernetes ConfigMap — stores the datasource configuration as a YAML string.

---

```yaml
# Lines 4-6
metadata:
  name: {{ include "simple-crud-app.fullname" . }}-loki-datasource
  namespace: {{ .Values.monitoring.loki.datasource.grafanaNamespace }}
```

- **`name`** — e.g., `crud-app-simple-crud-app-loki-datasource`. Suffixed to distinguish from the dashboard ConfigMap.
- **`namespace: monitoring`** — This ConfigMap is created in the **Grafana namespace**, NOT the app namespace. This is critical because the Grafana sidecar only watches ConfigMaps in its own namespace by default (unless `sidecar.datasources.searchNamespace=ALL` is set).

---

```yaml
# Lines 7-9
  labels:
    {{- include "simple-crud-app.labels" . | nindent 4 }}
    grafana_datasource: "1"
```

- **`simple-crud-app.labels`** — Standard chart labels.
- **`grafana_datasource: "1"`** — The magic label. The Grafana sidecar container (deployed by kube-prometheus-stack) continuously watches for ConfigMaps with this label. When it finds one, it reads the `data` section and provisions the datasource in Grafana.
- **Without this label**, Grafana never sees this ConfigMap.

---

```yaml
# Lines 10-11
data:
  loki-datasource.yaml: |-
```

- **`data:`** — The ConfigMap's data section. Each key becomes a "file" inside the ConfigMap.
- **`loki-datasource.yaml`** — The filename. The Grafana sidecar reads this as a datasource provisioning file.
- **`|-`** — YAML block scalar (literal, strip trailing newlines). Everything indented below is a single multi-line string. The `-` strips the final trailing newline.

---

```yaml
# Lines 12-13
    apiVersion: 1
    datasources:
```

- **`apiVersion: 1`** — Grafana's datasource provisioning format version (not Kubernetes API version). This is Grafana's own configuration format.
- **`datasources:`** — List of datasources to provision.

---

```yaml
# Line 14
      - name: Loki
```

- **`name: Loki`** — Display name in the Grafana UI. Appears in the datasource dropdown when editing panels.

---

```yaml
# Line 15
        type: loki
```

- **`type: loki`** — Tells Grafana which datasource plugin to use. Grafana has built-in support for Loki.

---

```yaml
# Line 16
        uid: loki
```

- **`uid: loki`** — A unique identifier for this datasource within Grafana.
- **Referenced by `grafana-dashboard.yaml`** — The Pod Logs panel explicitly sets `"datasource": { "type": "loki", "uid": "loki" }`. If you change the UID here, you must also update the dashboard.
- Using a fixed UID (instead of auto-generated) ensures the dashboard's datasource references remain valid across reinstalls.

---

```yaml
# Line 17
        access: proxy
```

- **`access: proxy`** — Grafana's server proxies requests to Loki on behalf of the browser.

| Mode | How it works | When to use |
|------|-------------|-------------|
| `proxy` | Browser → Grafana server → Loki | Default. Loki doesn't need to be browser-accessible |
| `direct` | Browser → Loki directly | Only if Loki is publicly accessible (rare) |

---

```yaml
# Line 18
        url: {{ .Values.monitoring.loki.datasource.url }}
```

- **`url: http://loki:3100`** — The in-cluster URL for the Loki service.
- `loki` is the Kubernetes Service name created by the loki-stack Helm chart.
- `3100` is Loki's default HTTP API port.
- Since `access: proxy`, Grafana's server (in the monitoring namespace) makes the request, so the DNS name `loki` resolves within the cluster.

---

```yaml
# Line 19
        isDefault: false
```

- **`isDefault: false`** — Loki is NOT the default datasource. Prometheus (installed by kube-prometheus-stack) is the default.
- Only one datasource can be default. Setting two as default causes a Grafana CrashLoopBackOff error.
- Panels without an explicit `datasource` field use the default (Prometheus). The Pod Logs panel explicitly specifies Loki.

---

```yaml
# Line 20
        editable: true
```

- **`editable: true`** — Users can modify this datasource's settings through the Grafana UI.
- If `false`, the datasource is locked and can only be changed by updating this ConfigMap.

---

```yaml
# Line 21
{{- end }}
```

- Closes the `if` guard from line 1.
