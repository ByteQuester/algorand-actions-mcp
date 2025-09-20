#!/usr/bin/env python3
"""
Quick test script to verify that all governance risk components can be imported correctly
"""

import sys
from pathlib import Path

# Add the core directory to the Python path
core_path = Path(__file__).parent / "core"
sys.path.insert(0, str(core_path))

def test_imports():
    """Test importing all core components"""
    try:
        # Test individual component imports
        print("Testing core component imports...")

        from governance_analyzer import GovernanceAnalyzer, RiskLevel, AttackVector
        print("✅ GovernanceAnalyzer imported successfully")

        from voting_concentration import VotingConcentrationAnalyzer, ConcentrationRiskLevel
        print("✅ VotingConcentrationAnalyzer imported successfully")

        from proposal_manipulation import ProposalManipulationDetector, ManipulationType
        print("✅ ProposalManipulationDetector imported successfully")

        from emergency_response import EmergencyResponseAnalyzer, EmergencyType
        print("✅ EmergencyResponseAnalyzer imported successfully")

        from upgrade_risks import ProtocolUpgradeRiskAnalyzer, UpgradeRiskLevel
        print("✅ ProtocolUpgradeRiskAnalyzer imported successfully")

        from regulatory_monitor import RegulatoryMonitor, RegulatoryEventType
        print("✅ RegulatoryMonitor imported successfully")

        from network_security import NetworkSecurityMetrics, SecurityRiskLevel
        print("✅ NetworkSecurityMetrics imported successfully")

        from foundation_dependency import FoundationDependencyAnalyzer, DependencyRiskLevel
        print("✅ FoundationDependencyAnalyzer imported successfully")

        from systemic_engine import SystemicRiskEngine, SystemicRiskLevel
        print("✅ SystemicRiskEngine imported successfully")

        print("\n🎉 All core components imported successfully!")

        # Test basic initialization
        print("\nTesting basic component initialization...")

        governance_analyzer = GovernanceAnalyzer()
        print("✅ GovernanceAnalyzer initialized")

        # Test configuration loading
        config = governance_analyzer.config
        if config and 'governance_risk' in config:
            print("✅ Configuration loaded successfully")
        else:
            print("⚠️  Using default configuration")

        # Test enum access
        print(f"✅ Risk levels available: {[level.value for level in RiskLevel]}")
        print(f"✅ Attack vectors available: {[vector.value for vector in AttackVector]}")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    try:
        print("\nTesting configuration system...")

        from governance_analyzer import GovernanceAnalyzer
        analyzer = GovernanceAnalyzer()

        config = analyzer.config
        required_sections = ['governance_risk', 'monitoring']

        for section in required_sections:
            if section in config:
                print(f"✅ Configuration section '{section}' found")
            else:
                print(f"⚠️  Configuration section '{section}' missing, using defaults")

        # Test specific configuration values
        governance_config = config.get('governance_risk', {})
        voting_config = governance_config.get('voting_concentration', {})

        critical_threshold = voting_config.get('critical_whale_threshold', 0.20)
        print(f"✅ Critical whale threshold: {critical_threshold}")

        return True

    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GOVERNANCE STABILITY RISK ASSESSMENT - IMPORT TEST")
    print("=" * 60)

    success = True

    # Test imports
    if not test_imports():
        success = False

    # Test configuration
    if not test_configuration():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - System is ready for use!")
        print("✅ You can now run the demo with: python3 demo_runner.py")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("=" * 60)

    sys.exit(0 if success else 1)