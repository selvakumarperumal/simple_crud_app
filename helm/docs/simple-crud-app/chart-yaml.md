# simple-crud-app / Chart.yaml — Documentation

**File:** [Chart.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/Chart.yaml)

---

## Line-by-Line Explanation

```yaml
# Line 1
apiVersion: v2
```

- Helm 3 chart format. `v2` is required for all Helm 3 charts. The older `v1` was Helm 2.

---

```yaml
# Line 2
name: simple-crud-app
```

- The chart name. Templates access this via `{{ .Chart.Name }}`.
- Used by `_helpers.tpl` to generate resource names (e.g., `<release>-simple-crud-app`).

---

```yaml
# Line 3
description: FastAPI CRUD application
```

- Human-readable description shown in `helm search`, `helm show chart`, and chart repositories.

---

```yaml
# Line 4
type: application
```

- `application` = this chart creates Kubernetes resources (Deployment, Service, etc.).
- The other option is `library` (shared templates only, no resources).

---

```yaml
# Line 5
version: 0.1.0
```

- **Chart version** (SemVer). Bump this when you change the chart templates, values structure, or any chart files.
- Independent from `appVersion`. You can update the chart without changing the app, and vice versa.

---

```yaml
# Line 6
appVersion: "0.1.0"
```

- Version of the FastAPI application inside the chart. Informational only.
- Quoted as a string (Helm requires `appVersion` to be a string).
- Shown in `helm list` output under the `APP VERSION` column.
- Does **not** control the Docker image tag — that's set in `values.yaml` → `image.tag`.
- The `_helpers.tpl` uses this in the `app.kubernetes.io/version` label.
