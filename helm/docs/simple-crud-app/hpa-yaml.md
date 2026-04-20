# simple-crud-app / templates/hpa.yaml — Documentation

**File:** [hpa.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/hpa.yaml)

---

## What Does This File Create?

A **HorizontalPodAutoscaler (HPA)** — automatically scales the number of pod replicas based on CPU utilization. Only created when `autoscaling.enabled: true`.

---

## Line-by-Line Explanation

```yaml
# Line 1
{{- if .Values.autoscaling.enabled }}
```

- **Guard** — Only rendered when `autoscaling.enabled` is `true`. Default is `false`.
- When this is `true`, the `deployment.yaml` omits its `replicas:` field to avoid conflicts with the HPA.

---

```yaml
# Lines 2-3
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
```

- **`autoscaling/v2`** — The stable HPA API (since Kubernetes 1.23). Supports multiple metrics (CPU, memory, custom metrics). The older `v1` only supported CPU.

---

```yaml
# Lines 4-7
metadata:
  name: {{ include "simple-crud-app.fullname" . }}
  labels:
    {{- include "simple-crud-app.labels" . | nindent 4 }}
```

- Standard metadata — same name as the Deployment, Service, etc.

---

```yaml
# Lines 8-12
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "simple-crud-app.fullname" . }}
```

- **`scaleTargetRef`** — Tells the HPA which resource to scale.
- Points to the Deployment created by `deployment.yaml` using the same `fullname`.
- The HPA adjusts the Deployment's `.spec.replicas` field up or down.

---

```yaml
# Lines 13-14
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
```

- **`minReplicas: 2`** — Never scale below 2 pods. Maintains redundancy even during low traffic.
- **`maxReplicas: 5`** — Never scale above 5 pods. Prevents runaway scaling and cost overruns.

---

```yaml
# Lines 15-21
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
```

- **`metrics`** — List of metrics the HPA uses to make scaling decisions.
- **`type: Resource`** — Uses a Kubernetes resource metric (CPU or memory), as opposed to custom or external metrics.
- **`name: cpu`** — Scale based on CPU usage.
- **`type: Utilization`** — Target is expressed as a percentage of the **requested** CPU.
- **`averageUtilization: 80`** — Scale up when the **average** CPU utilization across all pods exceeds 80% of the requested CPU.

**Scaling math example:**
- Each pod requests `100m` CPU (from values.yaml resources).
- 80% of 100m = 80m.
- If 2 pods are averaging 90m CPU each (90%), the HPA calculates: `ceil(2 × 90 / 80) = 3` → scales to 3 pods.
- If 3 pods are averaging 50m CPU (50%), HPA might scale back to 2 (after a cooldown period).

**Cooldown periods (defaults):**
- Scale up: 0 seconds (immediate).
- Scale down: 5 minutes (prevents flapping).

---

```yaml
# Line 22
{{- end }}
```

- Closes the `if .Values.autoscaling.enabled` guard.

---

## Prerequisites

The HPA requires **metrics-server** to be installed in the cluster:
- **Minikube:** `minikube addons enable metrics-server`
- **EKS:** metrics-server is installed by default.

Without metrics-server, the HPA will report `<unknown>` for CPU utilization and will not scale.
