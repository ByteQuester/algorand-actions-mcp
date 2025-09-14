#!/bin/bash

# 🚀 Algorand Lending Platform - Kubernetes Deployment Script
# Complete Kubernetes deployment with monitoring and security

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="algorand-lending"
KUBE_CONTEXT=""
DRY_RUN=false
SKIP_BUILD=false
IMAGE_TAG="latest"
REGISTRY=""
VERBOSE=false

# Default values
DOMAIN="${DOMAIN:-lending.example.com}"
CLUSTER_NAME="${CLUSTER_NAME:-algorand-lending}"

# Output functions
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

banner() {
    echo -e "${CYAN}$1${NC}"
}

# Usage information
usage() {
    cat << EOF
🚀 Algorand Lending Platform - Kubernetes Deployment

Usage: $0 [OPTIONS]

OPTIONS:
    --namespace <name>      Kubernetes namespace (default: algorand-lending)
    --context <context>     Kubectl context to use
    --registry <registry>   Container registry (required)
    --tag <tag>             Image tag (default: latest)
    --domain <domain>       Base domain for services
    --skip-build            Skip Docker image building
    --dry-run               Show what would be deployed
    --verbose               Verbose output
    --help                  Show this help message

EXAMPLES:
    $0 --registry gcr.io/my-project --domain lending.example.com
    $0 --context prod-cluster --tag v1.2.3 --registry my-registry.com
    $0 --dry-run --verbose

PREREQUISITES:
    - kubectl configured and connected to cluster
    - Docker registry access configured
    - Required secrets and configmaps prepared

EOF
}

# Check prerequisites
check_prerequisites() {
    info "Checking Kubernetes deployment prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl not found. Please install kubectl."
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
    fi

    # Check context
    if [[ -n "$KUBE_CONTEXT" ]]; then
        if ! kubectl config get-contexts "$KUBE_CONTEXT" &> /dev/null; then
            error "Kubernetes context '$KUBE_CONTEXT' not found."
        fi
        kubectl config use-context "$KUBE_CONTEXT"
        success "Using Kubernetes context: $KUBE_CONTEXT"
    fi

    # Check registry
    if [[ -z "$REGISTRY" ]]; then
        error "Container registry not specified. Use --registry option."
    fi

    # Check Docker if not skipping build
    if [[ "$SKIP_BUILD" != true ]] && ! command -v docker &> /dev/null; then
        error "Docker not found but image building is enabled. Use --skip-build or install Docker."
    fi

    # Check cluster resources
    local nodes=$(kubectl get nodes --no-headers | wc -l)
    if [[ $nodes -lt 1 ]]; then
        error "No nodes available in the cluster."
    fi

    success "Prerequisites check passed ($nodes nodes available)"
}

# Create namespace and RBAC
setup_namespace() {
    info "Setting up namespace and RBAC..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would create namespace: $NAMESPACE"
        return 0
    fi

    # Apply namespace configuration
    kubectl apply -f "$SCRIPT_DIR/namespace.yml"

    # Wait for namespace to be ready
    kubectl wait --for=condition=Active namespace/$NAMESPACE --timeout=60s

    success "Namespace '$NAMESPACE' configured"
}

# Build and push Docker images
build_and_push_images() {
    if [[ "$SKIP_BUILD" == true ]]; then
        info "Skipping Docker image building"
        return 0
    fi

    info "Building and pushing Docker images..."

    local project_root="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
    local images=(
        "algorand-lending-ui"
        "algorand-lending-api"
        "algorand-remote-mcp"
        "algorand-actions-mcp"
    )

    for image in "${images[@]}"; do
        local full_image="$REGISTRY/$image:$IMAGE_TAG"

        if [[ "$DRY_RUN" == true ]]; then
            info "[DRY-RUN] Would build and push: $full_image"
            continue
        fi

        info "Building image: $image"

        # Build image
        local dockerfile="deployments/docker/Dockerfile.${image/algorand-/}"
        docker build -t "$full_image" -f "$dockerfile" "$project_root"

        # Push image
        info "Pushing image: $full_image"
        docker push "$full_image"

        success "Built and pushed: $full_image"
    done
}

# Deploy ConfigMaps and Secrets
deploy_config() {
    info "Deploying configuration and secrets..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would deploy ConfigMaps and Secrets"
        return 0
    fi

    # Create temporary file with updated values
    local temp_config=$(mktemp)
    sed "s/yourdomain\.com/$DOMAIN/g" "$SCRIPT_DIR/configmaps-secrets.yml" > "$temp_config"

    kubectl apply -f "$temp_config"
    rm "$temp_config"

    success "Configuration deployed"
}

# Deploy PostgreSQL
deploy_postgresql() {
    info "Deploying PostgreSQL database..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would deploy PostgreSQL"
        return 0
    fi

    cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: algorand-lending
  labels:
    app: postgres
    component: database
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
        component: database
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: POSTGRES_PASSWORD
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2
            memory: 4Gi
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
            - -d
            - $(POSTGRES_DB)
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
            - -d
            - $(POSTGRES_DB)
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: algorand-lending
  labels:
    app: postgres
    component: database
spec:
  ports:
  - port: 5432
    targetPort: 5432
    name: postgres
  selector:
    app: postgres
  clusterIP: None
EOF

    # Wait for PostgreSQL to be ready
    kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s

    success "PostgreSQL deployed"
}

# Deploy Redis
deploy_redis() {
    info "Deploying Redis cache..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would deploy Redis"
        return 0
    fi

    cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: algorand-lending
  labels:
    app: redis
    component: cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
        component: cache
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: redis
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: REDIS_PASSWORD
        command:
        - redis-server
        - --requirepass
        - $(REDIS_PASSWORD)
        - --appendonly
        - "yes"
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
        volumeMounts:
        - name: redis-data
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: algorand-lending
  labels:
    app: redis
    component: cache
spec:
  ports:
  - port: 6379
    targetPort: 6379
    name: redis
  selector:
    app: redis
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data-pvc
  namespace: algorand-lending
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF

    kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=180s

    success "Redis deployed"
}

# Deploy application services
deploy_applications() {
    info "Deploying application services..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would deploy application services"
        return 0
    fi

    # Update image references in deployment files
    local temp_dir=$(mktemp -d)

    for file in "$SCRIPT_DIR"/*-deployment.yml; do
        if [[ -f "$file" ]]; then
            local basename=$(basename "$file")
            sed "s|image: algorand-|image: $REGISTRY/algorand-|g" "$file" | \
            sed "s|:latest|:$IMAGE_TAG|g" > "$temp_dir/$basename"

            kubectl apply -f "$temp_dir/$basename"
        fi
    done

    # Deploy additional services
    deploy_mcp_services
    deploy_ui_service

    # Wait for deployments to be ready
    info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available deployment --all -n $NAMESPACE --timeout=600s

    success "Application services deployed"
    rm -rf "$temp_dir"
}

# Deploy MCP services
deploy_mcp_services() {
    cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-reader
  namespace: algorand-lending
  labels:
    app: mcp-reader
    component: blockchain
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-reader
  template:
    metadata:
      labels:
        app: mcp-reader
        component: blockchain
    spec:
      containers:
      - name: mcp-reader
        image: $REGISTRY/algorand-remote-mcp:$IMAGE_TAG
        ports:
        - containerPort: 8002
          name: http
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "8002"
        - name: ALGORAND_NETWORK
          valueFrom:
            configMapKeyRef:
              name: algorand-config
              key: ALGORAND_NETWORK
        - name: ALGORAND_ALGOD_URL
          valueFrom:
            configMapKeyRef:
              name: algorand-config
              key: ALGORAND_ALGOD_URL
        - name: ALGORAND_INDEXER_URL
          valueFrom:
            configMapKeyRef:
              name: algorand-config
              key: ALGORAND_INDEXER_URL
        - name: READ_ONLY
          value: "true"
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-reader-service
  namespace: algorand-lending
  labels:
    app: mcp-reader
    component: blockchain
spec:
  ports:
  - port: 8002
    targetPort: 8002
    name: http
  selector:
    app: mcp-reader
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-writer
  namespace: algorand-lending
  labels:
    app: mcp-writer
    component: blockchain
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mcp-writer
  template:
    metadata:
      labels:
        app: mcp-writer
        component: blockchain
    spec:
      containers:
      - name: mcp-writer
        image: $REGISTRY/algorand-actions-mcp:$IMAGE_TAG
        ports:
        - containerPort: 3001
          name: http
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3001"
        - name: ALGORAND_NETWORK
          valueFrom:
            configMapKeyRef:
              name: algorand-config
              key: ALGORAND_NETWORK
        - name: ALGORAND_ALGOD_URL
          valueFrom:
            configMapKeyRef:
              name: algorand-config
              key: ALGORAND_ALGOD_URL
        - name: ALGORAND_INDEXER_URL
          valueFrom:
            configMapKeyRef:
              name: algorand-config
              key: ALGORAND_INDEXER_URL
        - name: READ_ONLY
          value: "false"
        - name: TRANSACTION_TIMEOUT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: TRANSACTION_TIMEOUT
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-writer-service
  namespace: algorand-lending
  labels:
    app: mcp-writer
    component: blockchain
spec:
  ports:
  - port: 3001
    targetPort: 3001
    name: http
  selector:
    app: mcp-writer
EOF
}

# Deploy UI service
deploy_ui_service() {
    cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lending-ui
  namespace: algorand-lending
  labels:
    app: lending-ui
    component: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lending-ui
  template:
    metadata:
      labels:
        app: lending-ui
        component: frontend
    spec:
      containers:
      - name: lending-ui
        image: $REGISTRY/algorand-lending-ui:$IMAGE_TAG
        ports:
        - containerPort: 8081
          name: http
        env:
        - name: NODE_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: NODE_ENV
        - name: PORT
          value: "8081"
        - name: API_BASE_URL
          value: "http://lending-api-service:80"
        - name: LENDING_ONLY_MODE
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LENDING_ONLY_MODE
        - name: HIDE_GENERIC_AGENTS
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: HIDE_GENERIC_AGENTS
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: lending-ui-service
  namespace: algorand-lending
  labels:
    app: lending-ui
    component: frontend
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8081
    name: http
  selector:
    app: lending-ui
EOF
}

# Deploy Ingress
deploy_ingress() {
    info "Deploying Ingress controller..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would deploy Ingress"
        return 0
    fi

    cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: algorand-lending-ingress
  namespace: algorand-lending
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rewrite-target: /\$1
spec:
  tls:
  - hosts:
    - $DOMAIN
    - api.$DOMAIN
    - grafana.$DOMAIN
    secretName: tls-secret
  rules:
  - host: $DOMAIN
    http:
      paths:
      - path: /(.*)
        pathType: Prefix
        backend:
          service:
            name: lending-ui-service
            port:
              number: 80
  - host: api.$DOMAIN
    http:
      paths:
      - path: /(.*)
        pathType: Prefix
        backend:
          service:
            name: lending-api-service
            port:
              number: 80
  - host: grafana.$DOMAIN
    http:
      paths:
      - path: /(.*)
        pathType: Prefix
        backend:
          service:
            name: grafana-service
            port:
              number: 3000
EOF

    success "Ingress configured for domain: $DOMAIN"
}

# Deploy monitoring stack
deploy_monitoring() {
    info "Deploying monitoring stack..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would deploy monitoring stack"
        return 0
    fi

    # Deploy Prometheus
    cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: algorand-lending
  labels:
    app: prometheus
    component: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
        component: monitoring
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.47.0
        ports:
        - containerPort: 9090
          name: http
        command:
        - '/bin/prometheus'
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--web.enable-lifecycle'
        - '--storage.tsdb.retention.time=30d'
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
          limits:
            cpu: 2
            memory: 4Gi
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-data
          mountPath: /prometheus
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /-/ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: prometheus-config
        configMap:
          name: monitoring-config
      - name: prometheus-data
        persistentVolumeClaim:
          claimName: prometheus-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: algorand-lending
  labels:
    app: prometheus
    component: monitoring
spec:
  ports:
  - port: 9090
    targetPort: 9090
    name: http
  selector:
    app: prometheus
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-data-pvc
  namespace: algorand-lending
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
EOF

    # Deploy Grafana
    cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: algorand-lending
  labels:
    app: grafana
    component: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
        component: monitoring
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:10.2.0
        ports:
        - containerPort: 3000
          name: http
        env:
        - name: GF_SECURITY_ADMIN_USER
          value: "admin"
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: monitoring-secret
              key: GRAFANA_ADMIN_PASSWORD
        - name: GF_SERVER_ROOT_URL
          value: "https://grafana.$DOMAIN"
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel"
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1
            memory: 2Gi
        volumeMounts:
        - name: grafana-data
          mountPath: /var/lib/grafana
        livenessProbe:
          httpGet:
            path: /api/health
            port: http
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: grafana-data
        persistentVolumeClaim:
          claimName: grafana-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: algorand-lending
  labels:
    app: grafana
    component: monitoring
spec:
  ports:
  - port: 3000
    targetPort: 3000
    name: http
  selector:
    app: grafana
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana-data-pvc
  namespace: algorand-lending
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF

    success "Monitoring stack deployed"
}

# Run post-deployment checks
run_post_deployment_checks() {
    info "Running post-deployment checks..."

    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would run post-deployment checks"
        return 0
    fi

    # Check all pods are running
    info "Checking pod status..."
    kubectl get pods -n $NAMESPACE

    # Wait for all pods to be ready
    local max_wait=600
    local wait_time=0

    while [[ $wait_time -lt $max_wait ]]; do
        local pending_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running --no-headers | wc -l)

        if [[ $pending_pods -eq 0 ]]; then
            success "All pods are running"
            break
        fi

        info "Waiting for $pending_pods pods to be ready... ($wait_time/$max_wait seconds)"
        sleep 10
        wait_time=$((wait_time + 10))
    done

    if [[ $wait_time -ge $max_wait ]]; then
        warning "Some pods may not be ready after $max_wait seconds"
    fi

    # Show services
    info "Service endpoints:"
    kubectl get services -n $NAMESPACE

    # Show ingress
    info "Ingress configuration:"
    kubectl get ingress -n $NAMESPACE

    success "Post-deployment checks completed"
}

# Display deployment summary
show_deployment_summary() {
    banner "🎉 Kubernetes Deployment Summary"
    echo
    info "Namespace: $NAMESPACE"
    info "Image Tag: $IMAGE_TAG"
    info "Registry: $REGISTRY"
    info "Domain: $DOMAIN"
    echo

    banner "📋 Access Information:"
    echo -e "  ${GREEN}Frontend:${NC}     https://$DOMAIN"
    echo -e "  ${GREEN}API:${NC}          https://api.$DOMAIN"
    echo -e "  ${GREEN}Grafana:${NC}      https://grafana.$DOMAIN"
    echo

    banner "🔧 Management Commands:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  kubectl get services -n $NAMESPACE"
    echo "  kubectl logs -f deployment/lending-api -n $NAMESPACE"
    echo "  kubectl scale deployment/lending-api --replicas=5 -n $NAMESPACE"
    echo

    banner "🔍 Monitoring:"
    echo "  kubectl port-forward service/prometheus-service 9090:9090 -n $NAMESPACE"
    echo "  kubectl port-forward service/grafana-service 3000:3000 -n $NAMESPACE"
    echo
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --context)
                KUBE_CONTEXT="$2"
                shift 2
                ;;
            --registry)
                REGISTRY="$2"
                shift 2
                ;;
            --tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    banner "🚀 Algorand Lending Platform - Kubernetes Deployment"
    echo

    parse_args "$@"
    check_prerequisites

    # Deployment phases
    setup_namespace
    build_and_push_images
    deploy_config
    deploy_postgresql
    deploy_redis
    deploy_applications
    deploy_ingress
    deploy_monitoring
    run_post_deployment_checks

    show_deployment_summary

    success "🎉 Deployment completed successfully!"
}

# Execute main function
main "$@"