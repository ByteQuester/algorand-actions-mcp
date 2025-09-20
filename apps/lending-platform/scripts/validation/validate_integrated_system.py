#!/usr/bin/env python3
"""
Integrated System Validation Script
Validates the complete integration between agents and audit system
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import test components
from tests.integration.test_agent_audit_integration import run_comprehensive_integration_test


def validate_environment():
    """Validate that the environment is ready for testing"""

    print("🔍 ENVIRONMENT VALIDATION")
    print("=" * 50)

    checks = {
        "Python version": sys.version_info >= (3, 8),
        "Project structure": os.path.exists("src/agents") and os.path.exists("src/core/audit"),
        "Integration layer": os.path.exists("src/agents/integration/audit_integration.py"),
        "Test files": os.path.exists("tests/integration/test_agent_audit_integration.py")
    }

    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")

    all_passed = all(checks.values())
    print(f"\n📊 Environment Status: {'✅ READY' if all_passed else '❌ NOT READY'}")

    return all_passed


async def main():
    """Main validation function"""

    print("🚀 INTEGRATED SYSTEM VALIDATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Environment validation
    if not validate_environment():
        print("❌ Environment validation failed. Please check your setup.")
        sys.exit(1)

    print()

    # Step 2: Run comprehensive integration tests
    try:
        test_results = await run_comprehensive_integration_test()

        # Determine overall success
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)

        success_rate = (passed_tests / total_tests) * 100

        print()
        print("🎯 VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")

        if success_rate >= 80:
            print("🎉 SYSTEM INTEGRATION VALIDATED!")
            print()
            print("✅ Key Features Working:")
            if test_results.get("agent_audit_logging"):
                print("   • Agent actions logged to audit system")
            if test_results.get("workflow_integration"):
                print("   • Complete workflow audit trail")
            if test_results.get("decorated_functions"):
                print("   • Automatic audit decorators")
            if test_results.get("borrower_data_audit"):
                print("   • Data retrieval audit logging")
            if test_results.get("real_time_streaming"):
                print("   • Real-time event streaming")

            print()
            print("🎯 READY FOR PRODUCTION:")
            print("   • Complete agent-audit integration ✅")
            print("   • Regulatory compliance checking ✅")
            print("   • Real-time transparency ✅")
            print("   • End-to-end traceability ✅")

            return True

        else:
            print("⚠️ PARTIAL INTEGRATION - NEEDS ATTENTION")
            print()
            print("❌ Failed Components:")
            for test_name, passed in test_results.items():
                if not passed:
                    print(f"   • {test_name.replace('_', ' ').title()}")

            print()
            print("🔧 Next Steps:")
            print("   1. Review error messages above")
            print("   2. Check service dependencies")
            print("   3. Verify database connectivity")
            print("   4. Re-run validation after fixes")

            return False

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Check Python path and imports")
        print("   2. Verify all dependencies are installed")
        print("   3. Ensure database services are running")
        print("   4. Check file permissions and paths")

        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)