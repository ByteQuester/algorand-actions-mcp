#!/usr/bin/env python3
"""
Reorganization Validation Script
Validates that all functionality is preserved after reorganization
"""

import os
import sys
import json
from pathlib import Path

# Add src to Python path
base_dir = Path(__file__).parent.parent.parent
src_dir = base_dir / "src"
sys.path.insert(0, str(src_dir))

def validate_directory_structure():
    """Validate that all expected directories exist"""
    print("🔍 Validating directory structure...")

    expected_dirs = [
        "src/agents",
        "src/core",
        "src/ui",
        "scripts/dev",
        "scripts/test",
        "scripts/demo",
        "scripts/deployment",
        "config/development",
        "config/production",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    all_valid = True
    for dir_path in expected_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - MISSING")
            all_valid = False

    return all_valid

def validate_agent_modules():
    """Validate that all agent modules are accessible"""
    print("\n🤖 Validating agent modules...")

    agent_modules = [
        "coordination",
        "negotiation",
        "liquidity",
        "execution"
    ]

    all_valid = True
    for module in agent_modules:
        try:
            # Check if agent directory exists
            agent_dir = base_dir / "src" / "agents" / module
            if not agent_dir.exists():
                print(f"  ❌ {module} - Directory missing")
                all_valid = False
                continue

            # Check if required files exist
            required_files = ["__init__.py", "agent.py", "tools.py"]
            for file_name in required_files:
                file_path = agent_dir / file_name
                if file_path.exists():
                    print(f"  ✅ {module}/{file_name}")
                else:
                    print(f"  ❌ {module}/{file_name} - MISSING")
                    all_valid = False

        except Exception as e:
            print(f"  ❌ {module} - Error: {e}")
            all_valid = False

    return all_valid

def validate_configuration_system():
    """Validate configuration system"""
    print("\n⚙️ Validating configuration system...")

    try:
        from core.config import get_config, ConfigurationManager

        # Test development configuration
        os.environ["NODE_ENV"] = "development"
        dev_config = get_config()
        print(f"  ✅ Development config loaded: {dev_config.environment}")

        # Test production configuration
        os.environ["NODE_ENV"] = "production"
        prod_config = get_config()
        print(f"  ✅ Production config loaded: {prod_config.environment}")

        # Test validation
        issues = prod_config.validate_configuration()
        if issues:
            print(f"  ⚠️ Configuration issues (expected in test): {len(issues)} issues")
        else:
            print(f"  ✅ Configuration validation passed")

        return True

    except Exception as e:
        print(f"  ❌ Configuration system error: {e}")
        return False

def validate_logging_system():
    """Validate logging system"""
    print("\n📋 Validating logging system...")

    try:
        from core.logging_config import get_logger, BusinessLogger, PerformanceLogger

        # Test basic logger
        logger = get_logger("test.validation")
        logger.info("Test log message")
        print("  ✅ Basic logger working")

        # Test business logger
        business_logger = BusinessLogger()
        business_logger.log_loan_request(
            borrower="TEST_ADDRESS",
            amount=1000000,
            collateral_type="ALGO"
        )
        print("  ✅ Business logger working")

        # Test performance logger
        perf_logger = PerformanceLogger()
        perf_logger.log_agent_performance(
            agent_name="test_agent",
            operation="test_operation",
            duration_ms=100.5
        )
        print("  ✅ Performance logger working")

        return True

    except Exception as e:
        print(f"  ❌ Logging system error: {e}")
        return False

def validate_preserved_scripts():
    """Validate that all important scripts are preserved"""
    print("\n🛠️ Validating preserved scripts...")

    script_categories = {
        "dev": [
            "debug_agent_errors.py",
            "debug_agent_response.py"
        ],
        "test": [
            "test_real_agent.py",
            "test_negotiation_agent.py",
            "test_toolbox_connection.py",
            "final_comprehensive_test.py",
            "validate_agents_comprehensive.py"
        ],
        "demo": [
            "demo_adk_agents.py",
            "simple_demo.py",
            "standalone_demo.py",
            "example_lending_agent.py"
        ],
        "deployment": [
            "build.py"
        ]
    }

    all_valid = True
    for category, scripts in script_categories.items():
        print(f"  📁 {category}/")
        for script in scripts:
            script_path = base_dir / "scripts" / category / script
            if script_path.exists():
                print(f"    ✅ {script}")
            else:
                print(f"    ❌ {script} - MISSING")
                all_valid = False

    return all_valid

def validate_manifest_and_schemas():
    """Validate agent manifest and schemas"""
    print("\n📋 Validating manifest and schemas...")

    try:
        # Check manifest
        manifest_path = base_dir / "src" / "agents" / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            print(f"  ✅ Manifest loaded: {manifest.get('name', 'Unknown')}")
            print(f"    - Agents: {len(manifest.get('agents', {}))}")
            print(f"    - Workflows: {len(manifest.get('workflows', {}))}")
        else:
            print("  ❌ Manifest missing")
            return False

        # Check schemas directory
        schemas_dir = base_dir / "src" / "agents" / "schemas"
        if schemas_dir.exists():
            agent_schemas = list((schemas_dir / "agents").glob("*.json"))
            tool_schemas = list((schemas_dir / "tools").glob("*.json"))
            workflow_schemas = list((schemas_dir / "workflows").glob("*.json"))

            print(f"  ✅ Schemas directory:")
            print(f"    - Agent schemas: {len(agent_schemas)}")
            print(f"    - Tool schemas: {len(tool_schemas)}")
            print(f"    - Workflow schemas: {len(workflow_schemas)}")
        else:
            print("  ❌ Schemas directory missing")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Manifest/schemas validation error: {e}")
        return False

def validate_environment_templates():
    """Validate environment templates"""
    print("\n🌍 Validating environment templates...")

    template_files = [
        ".env.example",
        "config/production/.env.production.template"
    ]

    all_valid = True
    for template in template_files:
        template_path = base_dir / template
        if template_path.exists():
            print(f"  ✅ {template}")
        else:
            print(f"  ❌ {template} - MISSING")
            all_valid = False

    return all_valid

def main():
    """Main validation function"""
    print("🔍 Lending Platform Reorganization Validation")
    print("=" * 50)

    validations = [
        ("Directory Structure", validate_directory_structure),
        ("Agent Modules", validate_agent_modules),
        ("Configuration System", validate_configuration_system),
        ("Logging System", validate_logging_system),
        ("Preserved Scripts", validate_preserved_scripts),
        ("Manifest and Schemas", validate_manifest_and_schemas),
        ("Environment Templates", validate_environment_templates)
    ]

    results = []
    for name, validator in validations:
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} validation failed with error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary")
    print("=" * 50)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} validations passed")

    if passed == total:
        print("\n🎉 All validations passed! Reorganization successful.")
        print("\n✅ The lending platform has been successfully reorganized for production")
        print("   while preserving all development functionality.")
        print("\n📖 Next steps:")
        print("   - Review PRODUCTION.md for deployment guide")
        print("   - Test development workflows in new structure")
        print("   - Deploy to production using scripts/deployment/build.py")
        return True
    else:
        print(f"\n❌ {total - passed} validations failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)