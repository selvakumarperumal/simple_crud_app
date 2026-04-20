# simple-crud-app / templates/service.yaml — Documentation

**File:** [service.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/service.yaml)

---

## What Does This File Create?

A Kubernetes **Service** — a stable network endpoint that routes traffic to the FastAPI pods. Pods are ephemeral (they get new IPs when restarted), but the Service provides a fixed DNS name and IP.

---

## Line-by-Line Explanation

```yaml
# Line 1
apiVersion: v1
```

- Core Kubernetes API. Services have been in `v1` since the beginning of Kubernetes.

---

```yaml
# Line 2
kind: Service
```

- Resource type. A Service provides network load balancing across a set of pods.

---

```yaml
# Lines 3-6
metadata:
  name: {{ include "simple-crud-app.fullname" . }}
  labels:
    {{- include "simple-crud-app.labels" . | nindent 4 }}
```

- **`name`** → e.g., `crud-app-simple-crud-app`. This becomes the DNS name: other pods can reach the app via `crud-app-simple-crud-app.<namespace>.svc.cluster.local` or just `crud-app-simple-crud-app` (within the same namespace).
- **`labels`** — Full label set for the Service resource itself.

---

```yaml
# Lines 7-8
spec:
  type: {{ .Values.service.type }}
```

- **`type: ClusterIP`** (default from values.yaml).

| Type | Accessibility | Use Case |
|------|--------------|----------|
| `ClusterIP` | Internal only (within cluster) | Default. Use with Ingress or port-forward |
| `NodePort` | External via `<NodeIP>:<NodePort>` | Minikube development |
| `LoadBalancer` | External via cloud load balancer | Production on AWS/GCP/Azure |

---

```yaml
# Lines 9-13
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
      protocol: TCP
      name: http
```

- **`port: 80`** — The port the Service listens on. Clients (including Ingress) connect to this port.
- **`targetPort: 8000`** — The port on the container where traffic is forwarded. Must match the container's `containerPort` in deployment.yaml (where uvicorn listens).
- **`protocol: TCP`** — TCP protocol (HTTP runs over TCP).
- **`name: http`** — Named port identifier. Referenced by:
  - `servicemonitor.yaml` → `endpoints[0].port: http`
  - `ingress.yaml` could reference it by name instead of number
  - Kubernetes documentation/debugging

**Traffic flow:**
```
Client → Service:80 (port) → Pod:8000 (targetPort) → uvicorn
```

---

```yaml
# Lines 14-15
  selector:
    {{- include "simple-crud-app.selectorLabels" . | nindent 4 }}
```

- **`selector`** — Determines which pods receive traffic from this Service.
- Uses **selectorLabels** (not full labels): `app.kubernetes.io/name: simple-crud-app` + `app.kubernetes.io/instance: crud-app`.
- Only pods whose labels match ALL of these selector labels receive traffic.
- This matches the `template.metadata.labels` in `deployment.yaml`, creating the connection:

```
Service (selector) ──matches──▶ Pod (labels) ◀──creates── Deployment (template)
```

---

## How Kubernetes Routes Traffic

When a request arrives at the Service:
1. `kube-proxy` (or eBPF on newer clusters) intercepts the connection.
2. It looks up the Service's **Endpoints** — the list of pod IPs whose labels match the selector.
3. It load-balances (round-robin by default) to one of the healthy pod IPs.
4. The request reaches the pod on `targetPort` (8000).

The readiness probe in `deployment.yaml` controls whether a pod appears in the Endpoints list. An unhealthy pod is removed from the list — the Service stops sending traffic to it.
