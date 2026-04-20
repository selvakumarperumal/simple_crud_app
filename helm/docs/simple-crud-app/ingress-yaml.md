# simple-crud-app / templates/ingress.yaml — Documentation

**File:** [ingress.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/ingress.yaml)

---

## What Does This File Create?

A Kubernetes **Ingress** — an HTTP routing rule that exposes the application externally via a domain name. It maps hostnames and URL paths to backend Services. Only created when `ingress.enabled: true`.

---

## Line-by-Line Explanation

```yaml
# Line 1
{{- if .Values.ingress.enabled }}
```

- **Guard** — The entire file is only rendered when `ingress.enabled` is `true` in values.yaml. Default is `false`, so no Ingress is created by default.

---

```yaml
# Lines 2-3
apiVersion: networking.k8s.io/v1
kind: Ingress
```

- `networking.k8s.io/v1` — Stable Ingress API (since Kubernetes 1.19). Older versions used `extensions/v1beta1` (deprecated).

---

```yaml
# Lines 4-7
metadata:
  name: {{ include "simple-crud-app.fullname" . }}
  labels:
    {{- include "simple-crud-app.labels" . | nindent 4 }}
```

- Standard metadata with full labels.

---

```yaml
# Lines 8-11
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
```

- **`ingressClassName`** — Specifies which Ingress controller handles this resource.
- Only rendered if `className` is non-empty (to avoid overriding cluster defaults).
- Common values:

| Value | Controller |
|-------|-----------|
| `nginx` | NGINX Ingress Controller |
| `alb` | AWS ALB Ingress Controller |
| `traefik` | Traefik |
| `istio` | Istio Gateway |

---

```yaml
# Lines 12-20
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
```

- **TLS section** — Configures HTTPS. Only rendered when `tls` is non-empty.
- **`range .Values.ingress.tls`** — Loops over each TLS configuration entry.
- **`range .hosts`** — Each TLS entry can cover multiple hostnames.
- **`{{ . | quote }}`** — Quotes the hostname string for YAML safety.
- **`secretName`** — References a Kubernetes Secret of type `kubernetes.io/tls` containing the TLS certificate and private key.
- **Example values.yaml for TLS:**
  ```yaml
  tls:
    - secretName: crud-app-tls
      hosts:
        - crud-app.example.com
  ```

---

```yaml
# Lines 22-36
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "simple-crud-app.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
```

- **`rules:`** — HTTP routing rules.
- **`range .Values.ingress.hosts`** — Loops over each host entry defined in values.yaml.
- **`host: "crud-app.local"`** — The domain name to match. Requests to this hostname are handled by this Ingress rule.
- **`range .paths`** — Each host can have multiple path rules.
- **`path: /`** — URL path to match.
- **`pathType: Prefix`** — Matching strategy:
  - `Prefix` — Matches URLs **starting with** this path (`/`, `/api`, `/api/v1/items`).
  - `Exact` — Matches the **exact** path only.
- **`backend.service`** — Where to route matched requests:
  - `name: {{ include "simple-crud-app.fullname" $ }}` — The Service created by `service.yaml`.
  - `port.number: {{ $.Values.service.port }}` — Port 80 (the Service port).

**`$` vs `.` inside `range`:**
- Inside a `range` loop, `.` refers to the **current loop item** (e.g., a single host object).
- `$` always refers to the **root context** (access to `.Values`, `.Release`, etc.).
- That's why line 32 uses `{{ include "simple-crud-app.fullname" $ }}` (needs root context) and line 24 uses `{{ .host }}` (needs current item).

---

```yaml
# Line 37
{{- end }}
```

- Closes the `if .Values.ingress.enabled` guard from line 1.

---

## Traffic Flow with Ingress

```
Internet → Ingress Controller (nginx/ALB) → Ingress rules → Service:80 → Pod:8000
```
