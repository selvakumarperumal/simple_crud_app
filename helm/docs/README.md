# Helm Charts Documentation

Detailed line-by-line documentation for every file in the `helm/` directory.

---

## Chart 1: `cnpg-cluster` (PostgreSQL Database)

| File | Description |
|------|-------------|
| [Chart.yaml](cnpg-cluster/chart-yaml.md) | Chart metadata — API version, name, type, versioning |
| [values.yaml](cnpg-cluster/values-yaml.md) | Default configuration — instances, storage, resources, monitoring |
| [templates/_helpers.tpl](cnpg-cluster/helpers-tpl.md) | Reusable named templates — name generation, standard labels |
| [templates/cluster.yaml](cnpg-cluster/cluster-yaml.md) | CNPG Cluster custom resource — bootstrap, storage, monitoring |

---

## Chart 2: `simple-crud-app` (FastAPI Application)

| File | Description |
|------|-------------|
| [Chart.yaml](simple-crud-app/chart-yaml.md) | Chart metadata — API version, name, type, versioning |
| [values.yaml](simple-crud-app/values-yaml.md) | Default configuration — image, service, ingress, autoscaling, database, monitoring |
| [values-monitoring.yaml](simple-crud-app/values-monitoring-yaml.md) | Monitoring overlay — enables ServiceMonitor, Grafana dashboard, Loki datasource |
| [templates/_helpers.tpl](simple-crud-app/helpers-tpl.md) | Reusable named templates — name, fullname, labels, selectorLabels |
| [templates/deployment.yaml](simple-crud-app/deployment-yaml.md) | Deployment — init container, env vars, sed URL rewrite, health probes |
| [templates/service.yaml](simple-crud-app/service-yaml.md) | Service — port mapping, selector labels, traffic routing |
| [templates/ingress.yaml](simple-crud-app/ingress-yaml.md) | Ingress — hostname routing, TLS, path matching, `$` vs `.` context |
| [templates/hpa.yaml](simple-crud-app/hpa-yaml.md) | HorizontalPodAutoscaler — CPU-based autoscaling |
| [templates/servicemonitor.yaml](simple-crud-app/servicemonitor-yaml.md) | ServiceMonitor — Prometheus scrape configuration |
| [templates/loki-datasource.yaml](simple-crud-app/loki-datasource-yaml.md) | Loki datasource — auto-provisioned in Grafana via sidecar |
| [templates/grafana-dashboard.yaml](simple-crud-app/grafana-dashboard-yaml.md) | Grafana dashboard — JSON model, PromQL queries, grid layout, escaping |

---

## How the Two Charts Connect

```mermaid
graph TD
    subgraph "cnpg-cluster chart"
        A["cluster.yaml"] -->|creates| B["CNPG Cluster: crud-db"]
        B -->|auto-creates| C["Secret: crud-db-app"]
        B -->|auto-creates| D["Service: crud-db-rw"]
    end

    subgraph "simple-crud-app chart"
        E["deployment.yaml"] -->|reads secret| C
        E -->|init container waits| D
        F["service.yaml"] -->|routes to| E
        G["ingress.yaml"] -->|routes to| F
        H["hpa.yaml"] -->|scales| E
        I["servicemonitor.yaml"] -->|scrapes via| F
        J["grafana-dashboard.yaml"] -->|queries| K["Prometheus"]
        J -->|queries| L["Loki"]
        M["loki-datasource.yaml"] -->|registers in| N["Grafana"]
    end

    I -->|metrics flow to| K
```

Both charts must be deployed in the **same namespace** (e.g., `crud`) for the database connection to work.
