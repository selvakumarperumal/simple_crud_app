# cnpg-cluster / templates/_helpers.tpl — Documentation

**File:** [_helpers.tpl](file:///home/selva/Documents/Terraform/simple_crud_app/helm/cnpg-cluster/templates/_helpers.tpl)

---

## What is _helpers.tpl?

A special Helm template file that defines reusable named templates. The `_` prefix means Helm will **not** render it as a Kubernetes manifest — it only provides helpers for other templates to call.

---

## Template 1: `cnpg-cluster.name` (Lines 1–3)

```yaml
{{- define "cnpg-cluster.name" -}}
{{- .Values.cluster.name | default "crud-db" | trunc 63 | trimSuffix "-" }}
{{- end }}
```

**Pipeline breakdown:**

| Step | What it does | Output |
|------|-------------|--------|
| `.Values.cluster.name` | Reads `name` from values.yaml | `"crud-db"` |
| `default "crud-db"` | Falls back to `"crud-db"` if value is empty/nil | `"crud-db"` |
| `trunc 63` | Truncates to 63 chars max (Kubernetes DNS name limit) | `"crud-db"` |
| `trimSuffix "-"` | Removes trailing `-` if truncation left one | `"crud-db"` |

The `{{-` and `-}}` dashes trim surrounding whitespace to prevent blank lines in output.

---

## Template 2: `cnpg-cluster.labels` (Lines 5–9)

```yaml
{{- define "cnpg-cluster.labels" -}}
app.kubernetes.io/name: {{ include "cnpg-cluster.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```

| Line | Label | Source | Example Value | Purpose |
|------|-------|--------|---------------|---------|
| 6 | `app.kubernetes.io/name` | Calls `cnpg-cluster.name` template | `crud-db` | Identifies the application |
| 7 | `app.kubernetes.io/instance` | `{{ .Release.Name }}` — the Helm release name | `crud-db` | Distinguishes multiple installs of the same chart |
| 8 | `app.kubernetes.io/managed-by` | `{{ .Release.Service }}` — always `"Helm"` in Helm 3 | `Helm` | Identifies which tool manages this resource |

---

## How These Are Called

In `cluster.yaml`:
```yaml
metadata:
  name: {{ include "cnpg-cluster.name" . }}
  labels:
    {{- include "cnpg-cluster.labels" . | nindent 4 }}
```

- **`include`** (not `template`) is used because it allows piping output to `nindent` for proper YAML indentation.
- **`| nindent 4`** — Adds a newline then indents every line by 4 spaces.
