#!/bin/bash
# Vendor Integrity Check Script
# Ensures no modifications have been made to vendor code

set -e

echo "🔍 Checking Vendor Directory Integrity..."
echo "========================================"

VENDOR_DIR="/home/mpo/algorand-showcase/vendor"
VIOLATIONS=0

# Function to report violations
report_violation() {
    echo "❌ VIOLATION: $1"
    VIOLATIONS=$((VIOLATIONS + 1))
}

# Function to check for success
report_success() {
    echo "✅ $1"
}

# Check if vendor directory exists
if [ ! -d "$VENDOR_DIR" ]; then
    report_violation "Vendor directory not found at $VENDOR_DIR"
    exit 1
fi

# Check for git modifications in vendor directory
echo ""
echo "📋 Checking for git modifications in vendor code..."

cd /home/mpo/algorand-showcase

# Check git status for vendor directory
VENDOR_CHANGES=$(git status --porcelain vendor/ | grep -v VENDOR_INFO.md | grep -v README.md || true)

if [ -n "$VENDOR_CHANGES" ]; then
    echo "❌ CRITICAL: Modified files detected in vendor directory:"
    echo "$VENDOR_CHANGES"
    echo ""
    echo "🚨 VENDOR CODE SHOULD NEVER BE MODIFIED!"
    echo "   - Revert these changes immediately"
    echo "   - Use overlay patterns instead"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    report_success "No unauthorized modifications in vendor directory"
fi

# Check for custom files in vendor directories
echo ""
echo "📋 Checking for custom files in vendor directories..."

CUSTOM_FILES=$(find vendor/ -name "*custom*" -o -name "*modified*" -o -name "*.backup" -o -name "*.orig" 2>/dev/null || true)

if [ -n "$CUSTOM_FILES" ]; then
    report_violation "Custom/modified files found in vendor directory:"
    echo "$CUSTOM_FILES"
else
    report_success "No custom files found in vendor directories"
fi

# Check for overlay files in wrong location
echo ""
echo "📋 Checking for overlay files in vendor location..."

OVERLAY_IN_VENDOR=$(find vendor/ -name "*lending*" -o -name "*overlay*" -o -name "*production*" 2>/dev/null | grep -v VENDOR_INFO.md || true)

if [ -n "$OVERLAY_IN_VENDOR" ]; then
    report_violation "Overlay files found in vendor directory:"
    echo "$OVERLAY_IN_VENDOR"
    echo "   - Move these to apps/lending-platform/ui-overlay/"
else
    report_success "No overlay files in vendor directory"
fi

# Check vendor documentation
echo ""
echo "📋 Checking vendor documentation..."

if [ -f "$VENDOR_DIR/README.md" ]; then
    report_success "Vendor README.md exists"
else
    report_violation "Missing vendor/README.md documentation"
fi

if [ -f "$VENDOR_DIR/google-adk-python/VENDOR_INFO.md" ]; then
    report_success "ADK Python vendor info exists"
else
    report_violation "Missing vendor/google-adk-python/VENDOR_INFO.md"
fi

# Check overlay structure exists
echo ""
echo "📋 Checking overlay structure..."

OVERLAY_DIR="/home/mpo/algorand-showcase/apps/lending-platform/ui-overlay"

if [ -d "$OVERLAY_DIR" ]; then
    report_success "Lending UI overlay directory exists"

    if [ -f "$OVERLAY_DIR/README.md" ]; then
        report_success "Overlay documentation exists"
    else
        report_violation "Missing overlay README.md"
    fi

    if [ -d "$OVERLAY_DIR/config" ]; then
        report_success "Overlay config directory exists"
    else
        report_violation "Missing overlay config directory"
    fi
else
    report_violation "Lending UI overlay directory missing"
fi

# Final report
echo ""
echo "========================================"
if [ $VIOLATIONS -eq 0 ]; then
    echo "🎉 VENDOR INTEGRITY CHECK PASSED!"
    echo "   ✅ No vendor code modifications"
    echo "   ✅ Clean separation maintained"
    echo "   ✅ Overlay structure correct"
    exit 0
else
    echo "🚨 VENDOR INTEGRITY CHECK FAILED!"
    echo "   ❌ $VIOLATIONS violations found"
    echo "   🔧 Fix these issues before proceeding"
    echo ""
    echo "💡 Remember:"
    echo "   - NEVER modify files in vendor/"
    echo "   - Use apps/lending-platform/ui-overlay/ for customizations"
    echo "   - Follow the overlay pattern"
    exit 1
fi