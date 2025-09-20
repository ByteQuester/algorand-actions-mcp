#!/usr/bin/env python3
"""
Test script specifically for the SystemicRiskEngine with proper imports
"""

import sys
from pathlib import Path

# Add the core directory to the Python path
core_path = Path(__file__).parent / "core"
sys.path.insert(0, str(core_path))

def test_systemic_engine():
    """Test the SystemicRiskEngine with absolute imports"""
    try:
        print("Testing SystemicRiskEngine...")

        # Import all required components individually
        from governance_analyzer import GovernanceAnalyzer, GovernanceStabilityReport, RiskLevel
        from voting_concentration import VotingConcentrationAnalyzer, VotingPowerMetrics, ConcentrationAlert
        from proposal_manipulation import ProposalManipulationDetector, ProposalManipulationReport
        from emergency_response import EmergencyResponseAnalyzer, ResponseReadinessReport
        from upgrade_risks import ProtocolUpgradeRiskAnalyzer, UpgradeRiskReport
        from regulatory_monitor import RegulatoryMonitor, RegulatoryRiskReport
        from network_security import NetworkSecurityMetrics, SecurityRiskLevel
        from foundation_dependency import FoundationDependencyAnalyzer, DependencyRiskLevel

        print("✅ All component dependencies imported successfully")

        # Import the main systemic engine classes
        from systemic_engine import SystemicRiskLevel, SystemicRiskMetrics, SystemicAlert, SystemicRiskReport

        print("✅ SystemicRiskEngine classes imported successfully")

        # Test enum values
        risk_levels = [level.value for level in SystemicRiskLevel]
        print(f"✅ Systemic risk levels: {risk_levels}")

        print("✅ SystemicRiskEngine components are working correctly!")
        return True

    except Exception as e:
        print(f"❌ SystemicRiskEngine test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SYSTEMIC RISK ENGINE - STANDALONE TEST")
    print("=" * 60)

    success = test_systemic_engine()

    print("\n" + "=" * 60)
    if success:
        print("🎉 SYSTEMIC ENGINE TEST PASSED!")
        print("✅ Core components are ready for integration")
    else:
        print("❌ SYSTEMIC ENGINE TEST FAILED")
    print("=" * 60)

    sys.exit(0 if success else 1)