#!/bin/bash

# Helm Deployment Script for Algorand MCP Workers
# Supports multi-environment deployment with validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_PATH="${SCRIPT_DIR}/charts/mcp-server"

# Default values
ENVIRONMENT=""
WORKER_TYPE=""
DRY_RUN=false
VALIDATE_ONLY=false
FORCE=false
NAMESPACE=""
RELEASE_NAME=""

# Usage function
usage() {
    echo "Usage: $0 -e ENVIRONMENT -w WORKER_TYPE [OPTIONS]"
    echo ""
    echo "Deploy Algorand MCP Workers using Helm"
    echo ""
    echo "Required Arguments:"
    echo "  -e, --environment ENV    Environment: development, staging, production"
    echo "  -w, --worker TYPE        Worker type: actions, remote, all"
    echo ""
    echo "Optional Arguments:"
    echo "  -n, --namespace NS       Kubernetes namespace (auto-generated if not provided)"
    echo "  -r, --release NAME       Helm release name (auto-generated if not provided)"
    echo "  -d, --dry-run           Perform dry run without actually deploying"
    echo "  -v, --validate          Validate configuration only"
    echo "  -f, --force             Force deployment even if validation fails"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e development -w all"
    echo "  $0 -e staging -w actions -d"
    echo "  $0 -e production -w remote -n algorand-mcp-prod"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -w|--worker)
            WORKER_TYPE="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--release)
            RELEASE_NAME="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--validate)
            VALIDATE_ONLY=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$ENVIRONMENT" || -z "$WORKER_TYPE" ]]; then
    echo -e "${RED}Error: Environment and worker type are required${NC}"
    usage
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}Error: Invalid environment. Must be: development, staging, production${NC}"
    exit 1
fi

# Validate worker type
if [[ ! "$WORKER_TYPE" =~ ^(actions|remote|all)$ ]]; then
    echo -e "${RED}Error: Invalid worker type. Must be: actions, remote, all${NC}"
    exit 1
fi

# Set default namespace if not provided
if [[ -z "$NAMESPACE" ]]; then
    NAMESPACE="algorand-mcp-${ENVIRONMENT}"
fi

echo -e "${BLUE}🚀 Algorand MCP Workers Deployment${NC}"
echo "=================================="
echo "Environment: $ENVIRONMENT"
echo "Worker Type: $WORKER_TYPE"
echo "Namespace: $NAMESPACE"
echo "Dry Run: $DRY_RUN"
echo "Validate Only: $VALIDATE_ONLY"
echo ""

# Check if Helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm is not installed${NC}"
    exit 1
fi

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ kubectl is not configured or cluster is not accessible${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Function to validate Helm chart
validate_chart() {
    echo -e "${YELLOW}🔍 Validating Helm chart...${NC}"

    if ! helm lint "$CHART_PATH"; then
        echo -e "${RED}❌ Helm chart validation failed${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Helm chart validation passed${NC}"
    return 0
}

# Function to validate values file
validate_values() {
    local worker="$1"
    local values_file="${SCRIPT_DIR}/${ENVIRONMENT}/${worker}-mcp-values.yaml"

    echo -e "${YELLOW}🔍 Validating values file: ${values_file}${NC}"

    if [[ ! -f "$values_file" ]]; then
        echo -e "${RED}❌ Values file not found: ${values_file}${NC}"
        return 1
    fi

    # Template rendering test
    local release_name="${worker}-mcp-${ENVIRONMENT}-test"
    if ! helm template "$release_name" "$CHART_PATH" -f "$values_file" > /dev/null; then
        echo -e "${RED}❌ Template rendering failed for ${worker}${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Values file validation passed for ${worker}${NC}"
    return 0
}

# Function to deploy worker
deploy_worker() {
    local worker="$1"
    local values_file="${SCRIPT_DIR}/${ENVIRONMENT}/${worker}-mcp-values.yaml"
    local release_name="${RELEASE_NAME:-${worker}-mcp-${ENVIRONMENT}}"

    echo -e "${YELLOW}🚀 Deploying ${worker} MCP Worker...${NC}"

    # Prepare Helm command
    local helm_cmd="helm"
    local action="install"

    # Check if release already exists
    if helm list -n "$NAMESPACE" | grep -q "^$release_name"; then
        action="upgrade"
        echo -e "${BLUE}📦 Release exists, upgrading...${NC}"
    else
        echo -e "${BLUE}📦 Creating new release...${NC}"
    fi

    # Build command
    helm_cmd="$helm_cmd $action $release_name $CHART_PATH"
    helm_cmd="$helm_cmd -f $values_file"
    helm_cmd="$helm_cmd --namespace $NAMESPACE"

    if [[ "$action" == "install" ]]; then
        helm_cmd="$helm_cmd --create-namespace"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        helm_cmd="$helm_cmd --dry-run"
    fi

    # Add additional options for production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        helm_cmd="$helm_cmd --wait --timeout=10m"
    fi

    echo -e "${BLUE}Running: ${helm_cmd}${NC}"

    # Execute deployment
    if eval "$helm_cmd"; then
        echo -e "${GREEN}✅ ${worker} MCP Worker deployed successfully${NC}"

        if [[ "$DRY_RUN" == "false" ]]; then
            # Show release status
            echo -e "${BLUE}📊 Release Status:${NC}"
            helm status "$release_name" -n "$NAMESPACE"

            # Show pod status
            echo -e "${BLUE}📊 Pod Status:${NC}"
            kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$release_name"
        fi

        return 0
    else
        echo -e "${RED}❌ ${worker} MCP Worker deployment failed${NC}"
        return 1
    fi
}

# Main deployment logic
main() {
    # Validate chart
    if ! validate_chart; then
        if [[ "$FORCE" == "false" ]]; then
            exit 1
        fi
        echo -e "${YELLOW}⚠️ Continuing despite chart validation failure (forced)${NC}"
    fi

    # Determine workers to deploy
    local workers=()
    if [[ "$WORKER_TYPE" == "all" ]]; then
        workers=("actions" "remote")
    else
        workers=("$WORKER_TYPE")
    fi

    # Validate values files
    local validation_failed=false
    for worker in "${workers[@]}"; do
        if ! validate_values "$worker"; then
            validation_failed=true
        fi
    done

    if [[ "$validation_failed" == "true" && "$FORCE" == "false" ]]; then
        echo -e "${RED}❌ Values validation failed${NC}"
        exit 1
    fi

    if [[ "$VALIDATE_ONLY" == "true" ]]; then
        echo -e "${GREEN}✅ Validation completed successfully${NC}"
        exit 0
    fi

    # Deploy workers
    local deployment_failed=false
    for worker in "${workers[@]}"; do
        if ! deploy_worker "$worker"; then
            deployment_failed=true
        fi
        echo ""
    done

    if [[ "$deployment_failed" == "true" ]]; then
        echo -e "${RED}❌ Some deployments failed${NC}"
        exit 1
    fi

    echo -e "${GREEN}🎉 All deployments completed successfully!${NC}"

    if [[ "$DRY_RUN" == "false" ]]; then
        echo ""
        echo "Next steps:"
        echo "  • Check status: kubectl get pods -n $NAMESPACE"
        echo "  • View logs: kubectl logs -f deployment/actions-mcp-${ENVIRONMENT} -n $NAMESPACE"
        echo "  • Test endpoints: kubectl port-forward svc/actions-mcp-${ENVIRONMENT} 8080:80 -n $NAMESPACE"
        echo "  • Monitor: helm status actions-mcp-${ENVIRONMENT} -n $NAMESPACE"
    fi
}

# Run main function
main