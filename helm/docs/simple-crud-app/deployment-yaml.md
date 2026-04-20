# simple-crud-app / templates/deployment.yaml — Documentation

**File:** [deployment.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/deployment.yaml)

---

## What Does This File Create?

A Kubernetes **Deployment** — the core resource that creates and manages the FastAPI application pods. It ensures the desired number of replicas are running and handles rolling updates.

---

## Line-by-Line Explanation

```yaml
# Line 1
apiVersion: apps/v1
```

- Kubernetes API group and version for the Deployment resource.
- `apps/v1` has been stable since Kubernetes 1.9.

---

```yaml
# Line 2
kind: Deployment
```

- Resource type. A Deployment manages a ReplicaSet which manages Pods. It provides declarative updates, rollback, and scaling.

---

```yaml
# Lines 3-6
metadata:
  name: {{ include "simple-crud-app.fullname" . }}
  labels:
    {{- include "simple-crud-app.labels" . | nindent 4 }}
```

- **`name`** — Calls the `fullname` helper → e.g., `crud-app-simple-crud-app`.
- **`labels`** — Full label set (chart version, app name, instance, managed-by). Applied to the Deployment **resource itself** (not the pods).
- **`| nindent 4`** — Newline + 4-space indent for proper YAML alignment under `labels:`.

---

```yaml
# Lines 7-10
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
```

- **`spec:`** — Desired state for the Deployment.
- **Conditional `replicas:`** — Only set the replica count when HPA is **disabled**. If HPA is enabled, it manages the replica count — setting it here would cause conflicts (Deployment resets to this value, HPA changes it, loop).
- **`replicas: 2`** — Run 2 pods by default.

---

```yaml
# Lines 11-13
  selector:
    matchLabels:
      {{- include "simple-crud-app.selectorLabels" . | nindent 6 }}
```

- **`selector.matchLabels`** — Tells the Deployment which pods it owns. Only pods with **both** `app.kubernetes.io/name: simple-crud-app` AND `app.kubernetes.io/instance: crud-app` are managed by this Deployment.
- **Immutable after creation** — you cannot change the selector on an existing Deployment.

---

```yaml
# Lines 14-17
  template:
    metadata:
      labels:
        {{- include "simple-crud-app.selectorLabels" . | nindent 8 }}
```

- **`template:`** — The pod template. Every pod created by this Deployment uses this template.
- **`metadata.labels`** — Pods get the **selector labels** (not full labels). These must match the `selector.matchLabels` above, or the Deployment rejects them.
- Indented by 8 spaces (`nindent 8`) because it's nested under `spec.template.metadata.labels`.

---

```yaml
# Lines 18-22
    spec:
      initContainers:
        - name: wait-for-pg
          image: busybox:1.36
          command: ["sh", "-c", "until nc -z {{ .Values.database.host }} {{ .Values.database.port }}; do echo waiting for postgres; sleep 2; done"]
```

- **`initContainers`** — Containers that run **before** the main app container starts. The app container won't start until all init containers succeed.
- **`wait-for-pg`** — An init container that waits for PostgreSQL to be ready:
  - **`busybox:1.36`** — Minimal Linux image with `nc` (netcat) included.
  - **`nc -z crud-db-rw 5432`** — Tests if TCP port 5432 is open on the `crud-db-rw` service (`-z` = scan only, don't send data).
  - **`until ... do ... done`** — Loops every 2 seconds until the connection succeeds.
  - **Why needed?** Without this, the app would crash immediately if the CNPG database isn't ready yet (e.g., during initial cluster creation which takes ~30-60 seconds).

---

```yaml
# Lines 23-30
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
```

- **`containers`** — The main application container.
- **`name: simple-crud-app`** — From `Chart.Name`.
- **`image: "simple-crud-app:latest"`** — Built from `repository:tag`. Quotes ensure special chars are safe.
- **`imagePullPolicy: IfNotPresent`** — From values.yaml.
- **`ports`:**
  - `name: http` — Named port. The Service, probes, and ServiceMonitor reference this name instead of the raw port number.
  - `containerPort: 8000` — The port uvicorn listens on inside the container.
  - `protocol: TCP` — Standard TCP (not UDP).

---

```yaml
# Lines 31-38
          env:
            - name: PG_URI
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.database.secretName }}
                  key: {{ .Values.database.secretKey }}
            - name: DATABASE_URL
              value: $(PG_URI)
```

- **`env`** — Environment variables injected into the container.
- **`PG_URI`** — Reads the PostgreSQL connection string from the Kubernetes Secret:
  - `name: crud-db-app` — The Secret created by CNPG.
  - `key: uri` — The key within the Secret containing the full URI: `postgresql://app:<password>@crud-db-rw:5432/crud_db`.
- **`DATABASE_URL: $(PG_URI)`** — Copies the value of `PG_URI` into `DATABASE_URL`. The `$(...)` syntax is **Kubernetes variable expansion** (not shell expansion) — it happens at pod startup before the container runs.
- **Why two variables?** The app reads `DATABASE_URL` (a common convention). `PG_URI` is an intermediate step because the Secret key is named `uri`, not `DATABASE_URL`.

---

```yaml
# Line 39
          command: ["sh", "-c", "export DATABASE_URL=$(echo $DATABASE_URL | sed 's|^postgresql://|postgresql+asyncpg://|'); exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

- **`command`** — Overrides the Docker image's default `CMD`.
- **The `sed` command** — Rewrites the database URL scheme:
  - **Input:** `postgresql://app:pass@crud-db-rw:5432/crud_db` (from CNPG Secret)
  - **Output:** `postgresql+asyncpg://app:pass@crud-db-rw:5432/crud_db`
  - **Why?** CNPG provides a standard `postgresql://` URI, but the app uses SQLAlchemy with the `asyncpg` driver, which requires the `+asyncpg` suffix in the scheme.
  - **`s|^postgresql://|postgresql+asyncpg://|`** — Substitution: replace `postgresql://` at the start of the string (`^`) with `postgresql+asyncpg://`. The `|` delimiter is used instead of `/` to avoid escaping the slashes in the URL.
- **`exec uvicorn app.main:app --host 0.0.0.0 --port 8000`**:
  - `exec` — Replaces the shell process with uvicorn (so uvicorn gets PID 1 and receives signals directly from Kubernetes).
  - `app.main:app` — The FastAPI application object in `app/main.py`.
  - `--host 0.0.0.0` — Listen on all interfaces (required in containers).
  - `--port 8000` — Must match `service.targetPort` in values.yaml.

---

```yaml
# Lines 40-45
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 15
```

- **Liveness probe** — Kubernetes checks if the container is still alive. If it fails, the container is **killed and restarted**.
- `httpGet` — Makes an HTTP GET request to `/health` on the named port `http` (8000).
- `initialDelaySeconds: 10` — Wait 10 seconds after container start before the first probe (gives the app time to boot).
- `periodSeconds: 15` — Check every 15 seconds after that.
- Default failure threshold is 3 — so the container is restarted after 3 consecutive failures (45 seconds of unhealthiness).

---

```yaml
# Lines 46-51
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
```

- **Readiness probe** — Kubernetes checks if the container is ready to receive traffic. If it fails, the pod is **removed from the Service's endpoints** (no traffic is routed to it) but the pod keeps running.
- `initialDelaySeconds: 5` — Shorter than liveness (5 vs 10) so the pod can start receiving traffic sooner once healthy.
- `periodSeconds: 10` — More frequent than liveness (10s vs 15s) for faster recovery when the pod becomes ready again.

**Liveness vs Readiness summary:**

| Probe | On failure | Use case |
|-------|-----------|----------|
| Liveness | Kill + restart the container | Detect deadlocks, hung processes |
| Readiness | Stop sending traffic | Detect temporary overload, DB connection loss |

---

```yaml
# Lines 52-53
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

- **`toYaml`** — Converts the `resources` object from values.yaml into YAML text.
- **`| nindent 12`** — 12 spaces of indentation (deeply nested under `spec.template.spec.containers[0].resources`).
- **Rendered:**
  ```yaml
            resources:
              requests:
                cpu: 100m
                memory: 128Mi
              limits:
                cpu: 500m
                memory: 256Mi
  ```
