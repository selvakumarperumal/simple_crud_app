# simple-crud-app / templates/_helpers.tpl — Documentation

**File:** [_helpers.tpl](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/_helpers.tpl)

---

## What is _helpers.tpl?

Defines reusable named templates. The `_` prefix tells Helm not to render this file as a Kubernetes manifest. All other templates call these helpers via `{{ include "template-name" . }}`.

---

## Template 1: `simple-crud-app.name` (Lines 1–3)

```yaml
{{- define "simple-crud-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}
```

**Pipeline:**

| Step | Function | Result |
|------|----------|--------|
| 1 | `default .Chart.Name .Values.nameOverride` | If `nameOverride` is set in values, use it; otherwise use `Chart.Name` (`simple-crud-app`) |
| 2 | `trunc 63` | Truncate to 63 chars (Kubernetes DNS limit) |
| 3 | `trimSuffix "-"` | Remove trailing dash if truncation created one |

**Default output:** `simple-crud-app`

**Override example:** `helm install ... --set nameOverride=myapp` → output: `myapp`

---

## Template 2: `simple-crud-app.fullname` (Lines 5–16)

```yaml
{{- define "simple-crud-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}
```

**Logic flow (3 branches):**

| Condition | Output | Example |
|-----------|--------|---------|
| `fullnameOverride` is set | Use it directly | `--set fullnameOverride=custom` → `custom` |
| Release name already contains chart name | Use release name only | `helm install simple-crud-app ...` → `simple-crud-app` (avoids `simple-crud-app-simple-crud-app`) |
| Default case | `<release>-<chart>` | `helm install crud-app ...` → `crud-app-simple-crud-app` |

**Why check `contains`?** To prevent stuttering names. If someone runs `helm install simple-crud-app ./simple-crud-app`, without this check the name would be `simple-crud-app-simple-crud-app`.

This fullname is used for **every resource name**: Deployment, Service, Ingress, HPA, ServiceMonitor, ConfigMaps.

---

## Template 3: `simple-crud-app.labels` (Lines 18–23)

```yaml
{{- define "simple-crud-app.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{ include "simple-crud-app.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

| Line | Label | Source | Example Value | Purpose |
|------|-------|--------|---------------|---------|
| 19 | `helm.sh/chart` | `Chart.Name-Chart.Version` with `+` replaced by `_` | `simple-crud-app-0.1.0` | Identifies the chart and version. `+` is replaced because labels can't contain `+` |
| 20 | *(includes selectorLabels)* | Calls Template 4 below | `app.kubernetes.io/name: simple-crud-app` + `app.kubernetes.io/instance: crud-app` | The selector labels are a subset of full labels |
| 21 | `app.kubernetes.io/version` | `Chart.AppVersion` quoted | `"0.1.0"` | Application version |
| 22 | `app.kubernetes.io/managed-by` | `Release.Service` | `Helm` | Tool managing the resource |

**Full rendered output:**
```yaml
helm.sh/chart: simple-crud-app-0.1.0
app.kubernetes.io/name: simple-crud-app
app.kubernetes.io/instance: crud-app
app.kubernetes.io/version: "0.1.0"
app.kubernetes.io/managed-by: Helm
```

---

## Template 4: `simple-crud-app.selectorLabels` (Lines 25–28)

```yaml
{{- define "simple-crud-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "simple-crud-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

| Label | Value | Purpose |
|-------|-------|---------|
| `app.kubernetes.io/name` | `simple-crud-app` | Identifies WHAT is deployed |
| `app.kubernetes.io/instance` | `crud-app` (release name) | Identifies WHICH installation |

**Why separate from full labels?**

Selector labels are used in `matchLabels` (Deployment → Pod, Service → Pod). These labels must be **immutable** across upgrades. If you included `helm.sh/chart` (which contains the version) in selectors, upgrading the chart version would change the selector and orphan existing pods.

**Used in:**
- `deployment.yaml` → `spec.selector.matchLabels` and `template.metadata.labels`
- `service.yaml` → `spec.selector`
- `servicemonitor.yaml` → `spec.selector.matchLabels`
