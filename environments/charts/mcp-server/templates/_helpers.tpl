{{/*
Expand the name of the chart.
*/}}
{{- define "mcp-server.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "mcp-server.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "mcp-server.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mcp-server.labels" -}}
helm.sh/chart: {{ include "mcp-server.chart" . }}
{{ include "mcp-server.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: {{ .Values.worker.type | default "mcp-worker" }}
app.kubernetes.io/part-of: algorand-mcp
{{- with .Values.common.labels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mcp-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mcp-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
worker.mcp/type: {{ .Values.worker.type }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mcp-server.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mcp-server.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the image name
*/}}
{{- define "mcp-server.image" -}}
{{- $registry := .Values.global.imageRegistry | default "" -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
Create worker-specific labels
*/}}
{{- define "mcp-server.workerLabels" -}}
worker.mcp/type: {{ .Values.worker.type }}
worker.mcp/name: {{ .Values.worker.name }}
{{- end }}

{{/*
Create worker-specific selector labels
*/}}
{{- define "mcp-server.workerSelectorLabels" -}}
{{ include "mcp-server.selectorLabels" . }}
worker.mcp/name: {{ .Values.worker.name }}
{{- end }}

{{/*
Determine if we should create a service account
*/}}
{{- define "mcp-server.createServiceAccount" -}}
{{- if .Values.serviceAccount.create -}}
{{- true -}}
{{- else -}}
{{- false -}}
{{- end -}}
{{- end }}

{{/*
Generate certificates for webhook if needed
*/}}
{{- define "mcp-server.webhook.certs" -}}
{{- $ca := genCA "mcp-server-ca" 365 -}}
{{- $cn := include "mcp-server.fullname" . -}}
{{- $altName1 := printf "%s.%s" $cn .Release.Namespace -}}
{{- $altName2 := printf "%s.%s.svc" $cn .Release.Namespace -}}
{{- $altName3 := printf "%s.%s.svc.cluster.local" $cn .Release.Namespace -}}
{{- $cert := genSignedCert $cn nil (list $altName1 $altName2 $altName3) 365 $ca -}}
caCert: {{ $ca.Cert | b64enc }}
clientCert: {{ $cert.Cert | b64enc }}
clientKey: {{ $cert.Key | b64enc }}
{{- end }}

{{/*
Get the ConfigMap name
*/}}
{{- define "mcp-server.configMapName" -}}
{{- printf "%s-config" (include "mcp-server.fullname" .) -}}
{{- end }}

{{/*
Get the Secret name
*/}}
{{- define "mcp-server.secretName" -}}
{{- printf "%s-secret" (include "mcp-server.fullname" .) -}}
{{- end }}

{{/*
Validate worker type
*/}}
{{- define "mcp-server.validateWorkerType" -}}
{{- $validTypes := list "actions" "remote" -}}
{{- if not (has .Values.worker.type $validTypes) -}}
{{- fail (printf "Invalid worker type: %s. Must be one of: %s" .Values.worker.type (join ", " $validTypes)) -}}
{{- end -}}
{{- end }}

{{/*
Generate environment-specific settings
*/}}
{{- define "mcp-server.environmentSettings" -}}
{{- if eq .Values.env.NODE_ENV "development" -}}
development: true
debug: true
{{- else if eq .Values.env.NODE_ENV "staging" -}}
staging: true
debug: false
{{- else -}}
production: true
debug: false
{{- end -}}
{{- end }}

{{/*
Calculate resource requests based on worker type and environment
*/}}
{{- define "mcp-server.resourceRequests" -}}
{{- if eq .Values.worker.type "actions" -}}
{{- if eq .Values.env.NODE_ENV "production" -}}
cpu: "200m"
memory: "256Mi"
{{- else -}}
cpu: "100m"
memory: "128Mi"
{{- end -}}
{{- else if eq .Values.worker.type "remote" -}}
{{- if eq .Values.env.NODE_ENV "production" -}}
cpu: "150m"
memory: "256Mi"
{{- else -}}
cpu: "100m"
memory: "128Mi"
{{- end -}}
{{- else -}}
cpu: "100m"
memory: "128Mi"
{{- end -}}
{{- end }}

{{/*
Calculate resource limits based on worker type and environment
*/}}
{{- define "mcp-server.resourceLimits" -}}
{{- if eq .Values.worker.type "actions" -}}
{{- if eq .Values.env.NODE_ENV "production" -}}
cpu: "1000m"
memory: "1Gi"
{{- else -}}
cpu: "500m"
memory: "512Mi"
{{- end -}}
{{- else if eq .Values.worker.type "remote" -}}
{{- if eq .Values.env.NODE_ENV "production" -}}
cpu: "800m"
memory: "1Gi"
{{- else -}}
cpu: "500m"
memory: "512Mi"
{{- end -}}
{{- else -}}
cpu: "500m"
memory: "512Mi"
{{- end -}}
{{- end }}