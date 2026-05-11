# simple-crud-app / templates/virtualservice.yaml — Documentation

**File:** [virtualservice.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/virtualservice.yaml)

---

## What Does This File Create?

An Istio **VirtualService** — defines the routing rules for traffic entering the mesh or communicating within it. It acts as the routing layer, replacing standard Kubernetes Ingress routing capabilities.

---

## Line-by-Line Explanation

```yaml
# Line 1
{{- if .Values.istio.enabled }}
```
- Only creates the VirtualService if `istio.enabled` is `true`.

```yaml
# Lines 2-3
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
```
- Istio custom resource definition for routing rules.

```yaml
# Lines 8-11
spec:
  hosts:
    {{- range .Values.istio.hosts }}
    - {{ . | quote }}
    {{- end }}
```
- `hosts` specifies the destination hosts to which traffic is being sent (e.g., `crud-app.local`).

```yaml
# Lines 12-17
  gateways:
    {{- if .Values.istio.gateway.create }}
    - {{ include "simple-crud-app.fullname" . }}
    {{- else if .Values.istio.gateway.name }}
    - {{ .Values.istio.gateway.name }}
    {{- end }}
```
- Attaches this VirtualService to an Istio Gateway. It either attaches to the one we just created, or a shared one defined in `values.yaml`.

```yaml
# Lines 18-24
  http:
    - match:
        - uri:
            prefix: /
      route:
        - destination:
            host: {{ include "simple-crud-app.fullname" . }}
            port:
              number: {{ .Values.service.port }}
```
- **`http.match`**: Matches all HTTP traffic hitting `/`.
- **`route.destination.host`**: Forwards the traffic to our Kubernetes Service.
- **`route.destination.port`**: Forwards to the Service's port (default 80).
