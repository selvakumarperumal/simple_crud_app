# simple-crud-app / templates/gateway.yaml — Documentation

**File:** [gateway.yaml](file:///home/selva/Documents/Terraform/simple_crud_app/helm/simple-crud-app/templates/gateway.yaml)

---

## What Does This File Create?

An Istio **Gateway** — configures a load balancer for HTTP/TCP traffic, most commonly operating at the edge of the mesh to enable ingress traffic for an application.

---

## Line-by-Line Explanation

```yaml
# Line 1
{{- if and .Values.istio.enabled .Values.istio.gateway.create }}
```
- Only creates the Gateway if `istio.enabled` is `true` AND `istio.gateway.create` is `true`.

```yaml
# Lines 2-3
apiVersion: networking.istio.io/v1beta1
kind: Gateway
```
- Istio custom resource definition for Gateways.

```yaml
# Lines 4-7
metadata:
  name: {{ include "simple-crud-app.fullname" . }}
  labels:
    {{- include "simple-crud-app.labels" . | nindent 4 }}
```
- Sets the name using the chart's standard fullname helper.

```yaml
# Lines 8-10
spec:
  selector:
    {{- toYaml .Values.istio.gateway.selector | nindent 4 }}
```
- `selector` determines which Istio ingress gateway pods should act on this configuration. Typically `istio: ingressgateway`.

```yaml
# Lines 11-15
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
```
- Configures the server to listen on port 80 for HTTP traffic.

```yaml
# Lines 16-19
      hosts:
        {{- range .Values.istio.hosts }}
        - {{ . | quote }}
        {{- end }}
```
- Binds this gateway to the specific hostnames provided in `values.yaml` (e.g., `crud-app.local`).
