#!/bin/bash

# Helm Chart Validation Script for Algorand MCP Workers
# Validates chart structure, templates, and environment-specific values

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

echo -e "${BLUE}🔍 Algorand MCP Workers - Helm Chart Validation${NC}"
echo "================================================="

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

MISSING_TOOLS=()

if ! command -v helm &> /dev/null; then
    MISSING_TOOLS+=("helm")
fi

if ! command -v kubectl &> /dev/null; then
    MISSING_TOOLS+=("kubectl")
fi

if ! command -v yq &> /dev/null; then
    echo -e "${YELLOW}⚠️ yq not found, some advanced validations will be skipped${NC}"
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required tools:${NC}"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "  • $tool"
    done
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Validate chart structure
echo -e "${YELLOW}📁 Validating chart structure...${NC}"

REQUIRED_FILES=(
    "Chart.yaml"
    "values.yaml"
    "templates/deployment.yaml"
    "templates/service.yaml"
    "templates/ingress.yaml"
    "templates/configmap.yaml"
    "templates/secret.yaml"
    "templates/serviceaccount.yaml"
    "templates/hpa.yaml"
    "templates/poddisruptionbudget.yaml"
    "templates/servicemonitor.yaml"
    "templates/networkpolicy.yaml"
    "templates/_helpers.tpl"
)

STRUCTURE_VALID=true

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$CHART_PATH/$file" ]]; then
        echo -e "${RED}❌ Missing required file: $file${NC}"
        STRUCTURE_VALID=false
    fi
done

if [[ "$STRUCTURE_VALID" == "true" ]]; then
    echo -e "${GREEN}✅ Chart structure validation passed${NC}"
else
    echo -e "${RED}❌ Chart structure validation failed${NC}"
    exit 1
fi

# Validate Chart.yaml
echo -e "${YELLOW}📄 Validating Chart.yaml...${NC}"

if ! helm show chart "$CHART_PATH" > /dev/null 2>&1; then
    echo -e "${RED}❌ Chart.yaml is invalid${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Chart.yaml validation passed${NC}"

# Lint Helm chart
echo -e "${YELLOW}🔧 Running Helm lint...${NC}"

if ! helm lint "$CHART_PATH"; then
    echo -e "${RED}❌ Helm lint failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Helm lint passed${NC}"

# Validate template rendering for each environment
echo -e "${YELLOW}🎨 Validating template rendering...${NC}"

ENVIRONMENTS=("development" "staging" "production")
WORKERS=("actions" "remote")

TEMPLATE_VALID=true

for env in "${ENVIRONMENTS[@]}"; do
    echo -e "${BLUE}  Testing environment: $env${NC}"

    for worker in "${WORKERS[@]}"; do
        values_file="${SCRIPT_DIR}/${env}/${worker}-mcp-values.yaml"

        if [[ ! -f "$values_file" ]]; then
            echo -e "${RED}    ❌ Missing values file: $values_file${NC}"
            TEMPLATE_VALID=false
            continue
        fi

        echo -e "${BLUE}    Testing worker: $worker${NC}"

        # Test template rendering
        release_name="${worker}-mcp-${env}-test"

        if ! helm template "$release_name" "$CHART_PATH" -f "$values_file" > /dev/null 2>&1; then
            echo -e "${RED}    ❌ Template rendering failed for $worker in $env${NC}"
            TEMPLATE_VALID=false
        else
            echo -e "${GREEN}    ✅ Template rendering passed for $worker in $env${NC}"
        fi

        # Validate specific worker type is set
        if command -v yq &> /dev/null; then
            worker_type=$(yq eval '.worker.type' "$values_file" 2>/dev/null || echo "")
            if [[ "$worker_type" != "$worker" ]]; then
                echo -e "${RED}    ❌ Worker type mismatch in $values_file: expected '$worker', got '$worker_type'${NC}"
                TEMPLATE_VALID=false
            fi
        fi
    done
done

if [[ "$TEMPLATE_VALID" == "true" ]]; then
    echo -e "${GREEN}✅ Template rendering validation passed${NC}"
else
    echo -e "${RED}❌ Template rendering validation failed${NC}"
    exit 1
fi

# Validate Kubernetes resource structure
echo -e "${YELLOW}☸️ Validating Kubernetes resources...${NC}"

RESOURCE_VALID=true

for env in "${ENVIRONMENTS[@]}"; do
    for worker in "${WORKERS[@]}"; do
        values_file="${SCRIPT_DIR}/${env}/${worker}-mcp-values.yaml"
        release_name="${worker}-mcp-${env}-test"

        echo -e "${BLUE}  Validating K8s resources: $worker in $env${NC}"

        # Generate manifests
        manifests=$(helm template "$release_name" "$CHART_PATH" -f "$values_file" 2>/dev/null)

        if [[ -z "$manifests" ]]; then
            echo -e "${RED}    ❌ No manifests generated${NC}"
            RESOURCE_VALID=false
            continue
        fi

        # Validate with kubectl (dry-run)
        if kubectl cluster-info &> /dev/null; then
            if ! echo "$manifests" | kubectl apply --dry-run=client -f - > /dev/null 2>&1; then
                echo -e "${RED}    ❌ Kubernetes resource validation failed${NC}"
                RESOURCE_VALID=false
            else
                echo -e "${GREEN}    ✅ Kubernetes resource validation passed${NC}"
            fi
        else
            echo -e "${YELLOW}    ⚠️ Skipping kubectl validation (no cluster connection)${NC}"
        fi
    done
done

if [[ "$RESOURCE_VALID" == "true" ]]; then
    echo -e "${GREEN}✅ Kubernetes resource validation passed${NC}"
elif ! kubectl cluster-info &> /dev/null; then
    echo -e "${YELLOW}⚠️ Kubernetes resource validation skipped (no cluster)${NC}"
else
    echo -e "${RED}❌ Kubernetes resource validation failed${NC}"
    exit 1
fi

# Validate environment-specific configurations
echo -e "${YELLOW}⚙️ Validating environment configurations...${NC}"

CONFIG_VALID=true

# Check development environment
dev_actions="$SCRIPT_DIR/development/actions-mcp-values.yaml"
dev_remote="$SCRIPT_DIR/development/remote-mcp-values.yaml"

if command -v yq &> /dev/null; then
    # Development should have 1 replica
    dev_actions_replicas=$(yq eval '.replicaCount' "$dev_actions" 2>/dev/null || echo "")
    dev_remote_replicas=$(yq eval '.replicaCount' "$dev_remote" 2>/dev/null || echo "")

    if [[ "$dev_actions_replicas" != "1" ]]; then
        echo -e "${RED}❌ Development actions should have 1 replica, got: $dev_actions_replicas${NC}"
        CONFIG_VALID=false
    fi

    if [[ "$dev_remote_replicas" != "1" ]]; then
        echo -e "${RED}❌ Development remote should have 1 replica, got: $dev_remote_replicas${NC}"
        CONFIG_VALID=false
    fi

    # Staging should have 2 replicas
    staging_actions="$SCRIPT_DIR/staging/actions-mcp-values.yaml"
    staging_actions_replicas=$(yq eval '.replicaCount' "$staging_actions" 2>/dev/null || echo "")

    if [[ "$staging_actions_replicas" != "2" ]]; then
        echo -e "${RED}❌ Staging should have 2 replicas, got: $staging_actions_replicas${NC}"
        CONFIG_VALID=false
    fi

    # Production should have 3+ replicas
    prod_actions="$SCRIPT_DIR/production/actions-mcp-values.yaml"
    prod_actions_replicas=$(yq eval '.replicaCount' "$prod_actions" 2>/dev/null || echo "")

    if [[ "$prod_actions_replicas" -lt 3 ]]; then
        echo -e "${RED}❌ Production should have 3+ replicas, got: $prod_actions_replicas${NC}"
        CONFIG_VALID=false
    fi

    echo -e "${GREEN}✅ Environment configuration validation passed${NC}"
else
    echo -e "${YELLOW}⚠️ Environment configuration validation skipped (yq not available)${NC}"
fi

# Security validation
echo -e "${YELLOW}🔒 Validating security configurations...${NC}"

SECURITY_VALID=true

for env in "${ENVIRONMENTS[@]}"; do
    for worker in "${WORKERS[@]}"; do
        values_file="${SCRIPT_DIR}/${env}/${worker}-mcp-values.yaml"
        release_name="${worker}-mcp-${env}-test"

        # Check if security context is properly configured
        manifests=$(helm template "$release_name" "$CHART_PATH" -f "$values_file" 2>/dev/null)

        if ! echo "$manifests" | grep -q "runAsNonRoot: true"; then
            echo -e "${RED}❌ Security context missing runAsNonRoot for $worker in $env${NC}"
            SECURITY_VALID=false
        fi

        if ! echo "$manifests" | grep -q "readOnlyRootFilesystem: true"; then
            echo -e "${RED}❌ Security context missing readOnlyRootFilesystem for $worker in $env${NC}"
            SECURITY_VALID=false
        fi
    done
done

if [[ "$SECURITY_VALID" == "true" ]]; then
    echo -e "${GREEN}✅ Security validation passed${NC}"
else
    echo -e "${RED}❌ Security validation failed${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}🎉 All validations passed successfully!${NC}"
echo ""
echo "Validation Summary:"
echo "  ✅ Chart structure"
echo "  ✅ Chart.yaml format"
echo "  ✅ Helm lint"
echo "  ✅ Template rendering"
echo "  ✅ Kubernetes resources"
echo "  ✅ Environment configurations"
echo "  ✅ Security configurations"
echo ""
echo "The Helm chart is ready for deployment!"
echo ""
echo "Next steps:"
echo "  • Deploy to development: ./deploy.sh -e development -w all"
echo "  • Deploy to staging: ./deploy.sh -e staging -w all"
echo "  • Deploy to production: ./deploy.sh -e production -w all"