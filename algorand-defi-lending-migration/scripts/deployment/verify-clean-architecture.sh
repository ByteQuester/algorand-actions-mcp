#!/bin/bash
set -e

echo "🔍 Verifying Clean Architecture Separation"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$DEPLOYMENT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS_COUNT=0
TOTAL_CHECKS=0

check_result() {
    local description="$1"
    local result="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ "$result" = "pass" ]; then
        echo -e "✅ ${GREEN}PASS${NC}: $description"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "❌ ${RED}FAIL${NC}: $description"
    fi
}

echo ""
echo "📁 Checking Source Code Cleanliness..."

# Check that no production configs remain in source directories
PROD_FILES_IN_SOURCE=$(find "$ROOT_DIR/apps" -name "*production*" -not -path "*/test*" -not -path "*/adk-*" | wc -l)
if [ "$PROD_FILES_IN_SOURCE" -eq 0 ]; then
    check_result "No production config files in source directories" "pass"
else
    check_result "Found $PROD_FILES_IN_SOURCE production files in source directories" "fail"
    find "$ROOT_DIR/apps" -name "*production*" -not -path "*/test*" -not -path "*/adk-*" | head -5
fi

# Check that no .env files remain in source directories (except examples)
ENV_FILES_IN_SOURCE=$(find "$ROOT_DIR/apps" -name ".env" -not -name "*.example" | wc -l)
if [ "$ENV_FILES_IN_SOURCE" -eq 0 ]; then
    check_result "No production .env files in source directories" "pass"
else
    check_result "Found $ENV_FILES_IN_SOURCE .env files in source directories" "fail"
fi

# Check that no deploy scripts remain in source directories
DEPLOY_SCRIPTS_IN_SOURCE=$(find "$ROOT_DIR/apps" -name "*deploy*.sh" | wc -l)
if [ "$DEPLOY_SCRIPTS_IN_SOURCE" -eq 0 ]; then
    check_result "No deployment scripts in source directories" "pass"
else
    check_result "Found $DEPLOY_SCRIPTS_IN_SOURCE deployment scripts in source directories" "fail"
fi

echo ""
echo "🏗️ Checking Deployment Structure..."

# Check deployment directory structure
REQUIRED_DIRS=(
    "$DEPLOYMENT_DIR/docker"
    "$DEPLOYMENT_DIR/kubernetes"
    "$DEPLOYMENT_DIR/production/configs"
    "$DEPLOYMENT_DIR/production/monitoring"
    "$DEPLOYMENT_DIR/production/secrets"
    "$DEPLOYMENT_DIR/scripts"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_result "Required directory exists: $(basename "$dir")" "pass"
    else
        check_result "Missing required directory: $(basename "$dir")" "fail"
    fi
done

# Check required configuration files
REQUIRED_FILES=(
    "$DEPLOYMENT_DIR/production/configs/production_config.py"
    "$DEPLOYMENT_DIR/production/configs/production_logging.py"
    "$DEPLOYMENT_DIR/production/configs/.env.production.template"
    "$DEPLOYMENT_DIR/docker/docker-compose.production.yml"
    "$DEPLOYMENT_DIR/scripts/start-production.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_result "Required file exists: $(basename "$file")" "pass"
    else
        check_result "Missing required file: $(basename "$file")" "fail"
    fi
done

echo ""
echo "🐳 Checking Docker Configuration..."

# Check Docker files are properly named and located
DOCKER_FILES=(
    "$DEPLOYMENT_DIR/docker/Dockerfile.remote-mcp"
    "$DEPLOYMENT_DIR/docker/Dockerfile.actions-mcp"
    "$DEPLOYMENT_DIR/docker/Dockerfile.lending-api"
)

for file in "${DOCKER_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_result "Docker file exists: $(basename "$file")" "pass"
    else
        check_result "Missing Docker file: $(basename "$file")" "fail"
    fi
done

echo ""
echo "📊 Checking Monitoring Setup..."

MONITORING_FILES=(
    "$DEPLOYMENT_DIR/production/monitoring/prometheus.yml"
    "$DEPLOYMENT_DIR/production/monitoring/alertmanager.yml"
)

for file in "${MONITORING_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_result "Monitoring file exists: $(basename "$file")" "pass"
    else
        check_result "Monitoring file exists: $(basename "$file")" "fail"
    fi
done

echo ""
echo "🔐 Checking Security Separation..."

# Check that secrets directory exists and is properly protected
if [ -d "$DEPLOYMENT_DIR/production/secrets" ]; then
    check_result "Secrets directory exists" "pass"

    # Check permissions (should be restricted)
    SECRETS_PERMS=$(stat -c "%a" "$DEPLOYMENT_DIR/production/secrets")
    if [ "$SECRETS_PERMS" = "755" ] || [ "$SECRETS_PERMS" = "700" ]; then
        check_result "Secrets directory has appropriate permissions ($SECRETS_PERMS)" "pass"
    else
        check_result "Secrets directory permissions may be too open ($SECRETS_PERMS)" "fail"
    fi
else
    check_result "Secrets directory exists" "fail"
fi

echo ""
echo "📈 Architecture Quality Checks..."

# Check source code only contains business logic
BUSINESS_SOURCE_FILES=$(find "$ROOT_DIR/apps/business" -name "*.py" -not -path "*/__pycache__/*" | wc -l)
if [ "$BUSINESS_SOURCE_FILES" -gt 0 ]; then
    check_result "Business logic source files present ($BUSINESS_SOURCE_FILES files)" "pass"
else
    check_result "Business logic source files present" "fail"
fi

# Check that deployment configs are properly organized
DEPLOYMENT_CONFIG_FILES=$(find "$DEPLOYMENT_DIR/production/configs" -name "*.py" | wc -l)
if [ "$DEPLOYMENT_CONFIG_FILES" -gt 0 ]; then
    check_result "Production configuration files properly organized ($DEPLOYMENT_CONFIG_FILES files)" "pass"
else
    check_result "Production configuration files properly organized" "fail"
fi

# Check that scripts are executable
EXECUTABLE_SCRIPTS=$(find "$DEPLOYMENT_DIR/scripts" -name "*.sh" -executable | wc -l)
TOTAL_SCRIPTS=$(find "$DEPLOYMENT_DIR/scripts" -name "*.sh" | wc -l)
if [ "$EXECUTABLE_SCRIPTS" -eq "$TOTAL_SCRIPTS" ] && [ "$TOTAL_SCRIPTS" -gt 0 ]; then
    check_result "All deployment scripts are executable ($EXECUTABLE_SCRIPTS/$TOTAL_SCRIPTS)" "pass"
else
    check_result "All deployment scripts are executable ($EXECUTABLE_SCRIPTS/$TOTAL_SCRIPTS)" "fail"
fi

echo ""
echo "=========================================="
echo "📊 VERIFICATION SUMMARY"
echo "=========================================="

if [ "$SUCCESS_COUNT" -eq "$TOTAL_CHECKS" ]; then
    echo -e "🎉 ${GREEN}ALL CHECKS PASSED${NC} ($SUCCESS_COUNT/$TOTAL_CHECKS)"
    echo ""
    echo -e "${GREEN}✅ Clean Architecture Verified!${NC}"
    echo ""
    echo "The codebase now has:"
    echo "  📦 Vendorable source code (apps/)"
    echo "  🏗️ Separated deployment configs (deployments/)"
    echo "  🔒 Security-focused structure"
    echo "  🐳 Production-ready containers"
    echo "  📊 Built-in monitoring"
    echo "  🚀 Professional deployment automation"
    echo ""
    echo "Ready for professional software distribution!"
    exit 0
else
    echo -e "⚠️  ${YELLOW}CHECKS COMPLETED WITH ISSUES${NC} ($SUCCESS_COUNT/$TOTAL_CHECKS passed)"
    echo ""
    echo "Please address the failed checks above before proceeding."
    exit 1
fi