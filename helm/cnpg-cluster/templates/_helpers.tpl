{{- define "cnpg-cluster.name" -}}
{{- .Values.cluster.name | default "crud-db" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "cnpg-cluster.labels" -}}
app.kubernetes.io/name: {{ include "cnpg-cluster.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
