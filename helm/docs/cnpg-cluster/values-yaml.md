# cnpg-cluster / values.yaml — Line-by-Line Documentation

**File:** [values.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/cnpg-cluster/values.yaml)

---

## What is values.yaml?

`values.yaml` is the **default configuration** file for a Helm chart. Every key defined here becomes accessible in templates via `{{ .Values.<key> }}`. Users can override any value at install time using `--set` flags or `-f custom-values.yaml`.

---

## Full File with Annotations

```yaml
# Line 1
cluster:
```

- **What:** Top-level grouping key for all CNPG cluster configuration.
- **Why a nested structure?** Grouping under `cluster:` keeps values organized and avoids name collisions. All templates access these via `{{ .Values.cluster.<field> }}`.

---

```yaml
# Line 2
  name: crud-db
```

- **What:** The name of the CloudNativePG `Cluster` Kubernetes resource.
- **Accessed by:** `{{ .Values.cluster.name }}` in `_helpers.tpl` → `cnpg-cluster.name` template.
- **Important side effects — CNPG auto-creates resources based on this name:**

| Auto-created resource | Name pattern | Purpose |
|-----------------------|-------------|---------|
| **Secret** | `crud-db-app` | Contains PostgreSQL connection URI, username, password |
| **Service (read-write)** | `crud-db-rw` | Routes to the primary instance |
| **Service (read-only)** | `crud-db-ro` | Routes to standby replicas |
| **Service (any)** | `crud-db-r` | Routes to any instance |
| **Pods** | `crud-db-1`, `crud-db-2` | The actual PostgreSQL instances |
| **PVCs** | `crud-db-1`, `crud-db-2` | Persistent storage per instance |

- **The `simple-crud-app` chart references `crud-db-app` (secret) and `crud-db-rw` (service)** — so changing this name requires updating the app chart's `values.yaml` too.

---

```yaml
# Line 3
  instances: 2
```

- **What:** Number of PostgreSQL instances to create.
- **How CNPG handles instances:**
  - **1 instance:** Single primary, no high availability. Good for development/minikube.
  - **2 instances:** 1 primary + 1 standby with automatic streaming replication. If the primary fails, CNPG promotes the standby automatically.
  - **3 instances:** 1 primary + 2 standbys. Provides better read scalability and survives a single-node failure while maintaining a replica.
- **Override for minikube:** `--set cluster.instances=1` (saves resources).

---

```yaml
# Line 4
  imageName: ghcr.io/cloudnative-pg/postgresql:16
```

- **What:** The full Docker image reference for PostgreSQL.
- **Breakdown:**
  - `ghcr.io` — GitHub Container Registry.
  - `cloudnative-pg/postgresql` — The official CNPG-maintained PostgreSQL image.
  - `:16` — PostgreSQL major version 16.
- **Why not use the official `postgres:16` image?** The CNPG image includes extra tooling for backup, recovery, and monitoring that the CNPG operator requires.
- **To upgrade PostgreSQL:** Change the tag to `:17` (when available). CNPG handles rolling upgrades automatically.

---

```yaml
# Line 5 (blank line for readability)
```

---

```yaml
# Line 6
  database: crud_db
```

- **What:** The name of the PostgreSQL database created during initial bootstrap.
- **When it runs:** Only once — when the cluster is first created. CNPG runs `CREATE DATABASE crud_db` via the `initdb` bootstrap method.
- **Referenced by:** The Grafana dashboard's CNPG panel queries filter by `datname="crud_db"`.
- **Cannot be changed after creation** without manual intervention (it's a bootstrap-only setting).

---

```yaml
# Line 7
  owner: app
```

- **What:** The PostgreSQL user (role) who owns the `crud_db` database.
- **What CNPG does:**
  1. Creates a PostgreSQL role named `app`.
  2. Generates a random password for it.
  3. Stores the credentials in the Kubernetes Secret `crud-db-app`.
  4. Grants `app` ownership of `crud_db`.
- **The app uses this user** — the Secret's `uri` key contains: `postgresql://app:<generated-password>@crud-db-rw:5432/crud_db`.

---

```yaml
# Lines 8 (blank line)
```

---

```yaml
# Line 9-11
  storage:
    size: 1Gi
    storageClass: ""
```

- **`storage:`** — Configuration for the Persistent Volume Claim (PVC) created for each PostgreSQL instance.

- **`size: 1Gi`**
  - Each PostgreSQL pod gets a **1 GiB** persistent volume.
  - This stores the PostgreSQL data directory (`PGDATA`).
  - **For production:** Increase to `10Gi` or more depending on data volume.
  - **Can be expanded later** (if the StorageClass supports volume expansion): change the value and `helm upgrade`.

- **`storageClass: ""`**
  - Empty string means **use the cluster's default StorageClass**.
  - On **Minikube:** defaults to `standard` (hostPath provisioner).
  - On **EKS:** defaults to `gp2` (EBS). You may want to set `gp3` for better performance/cost.
  - The template only renders the `storageClass` field if this value is non-empty (see `cluster.yaml` line 18-20).

---

```yaml
# Lines 12 (blank line)
```

---

```yaml
# Lines 13-19
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: "1"
      memory: 512Mi
```

- **`resources:`** — Kubernetes resource requests and limits for each PostgreSQL pod.

- **`requests`** — Guaranteed minimum resources the pod is scheduled with:
  - `cpu: 100m` — 0.1 CPU cores (100 millicores). The Kubernetes scheduler ensures at least this much CPU is available on the node.
  - `memory: 256Mi` — 256 MiB of RAM. If the node doesn't have this much free memory, the pod won't be scheduled.

- **`limits`** — Maximum resources the pod can use:
  - `cpu: "1"` — 1 full CPU core. Quoted as a string because YAML would interpret bare `1` as an integer, but Kubernetes expects a string for resource quantities. The pod is CPU-throttled if it tries to exceed this.
  - `memory: 512Mi` — 512 MiB. If the pod exceeds this, it is **OOM-killed** (Out Of Memory killed) by the kernel.

- **Why requests < limits?** This is called **burstable** QoS class. The pod normally uses ~100m CPU but can burst up to 1 core during heavy queries. Setting requests = limits would make it **guaranteed** QoS (more predictable but wastes resources).

---

```yaml
# Lines 20 (blank line)
```

---

```yaml
# Lines 21-22
  monitoring:
    enabled: false
```

- **`monitoring.enabled: false`** — When `true`, the `cluster.yaml` template adds a `monitoring.enablePodMonitor: true` section to the CNPG Cluster spec.
- **What a PodMonitor does:** It's a Prometheus Operator CRD that tells Prometheus to scrape PostgreSQL metrics directly from the CNPG pods (port 9187, the built-in metrics exporter).
- **Metrics exposed include:** `cnpg_pg_stat_database_xact_commit` (transactions/sec), `cnpg_pg_replication_lag` (replication lag), etc.
- **The Grafana dashboard's CNPG panels** depend on these metrics — if monitoring is disabled here, those panels will show "No data".
- **Default is `false`** because it requires the Prometheus Operator to be installed in the cluster first.

---

## Override Examples

```bash
# Minikube: single instance, smaller storage
helm install crud-db helm/cnpg-cluster -n crud --create-namespace \
  --set cluster.instances=1 \
  --set cluster.storage.size=512Mi

# EKS production: 3 instances, gp3 storage, more resources
helm install crud-db helm/cnpg-cluster -n crud --create-namespace \
  --set cluster.instances=3 \
  --set cluster.storage.size=20Gi \
  --set cluster.storage.storageClass=gp3 \
  --set cluster.resources.requests.memory=1Gi \
  --set cluster.resources.limits.memory=2Gi \
  --set cluster.monitoring.enabled=true
```
