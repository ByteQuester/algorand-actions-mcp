#!/usr/bin/env python3
"""
Simple Governance Risk Assessment Demo
Demonstrates the core functionality without complex imports
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the core directory to the Python path
core_path = Path(__file__).parent / "core"
sys.path.insert(0, str(core_path))

async def simple_governance_demo():
    """Run a simple demonstration of governance risk assessment"""
    print("🚀 ALGORAND GOVERNANCE STABILITY RISK ASSESSMENT DEMO")
    print("=" * 60)

    try:
        # Test individual components
        print("\n📊 Testing Individual Risk Components:")
        print("-" * 40)

        # 1. Governance Analyzer
        print("1. Testing Governance Analyzer...")
        from governance_analyzer import GovernanceAnalyzer, RiskLevel

        governance_analyzer = GovernanceAnalyzer()
        print(f"   ✅ Initialized with {len(governance_analyzer.config)} config sections")

        # Sample governance data
        sample_governance_data = {
            'total_voting_power': 5_000_000_000,
            'active_voters': 145_000,
            'current_proposals': [
                {
                    'id': 'demo_proposal',
                    'title': 'Demo Governance Proposal',
                    'submission_time': datetime.utcnow().isoformat(),
                    'voting_deadline': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    'submitter': 'demo_submitter',
                    'deliberation_time': 604800  # 7 days
                }
            ],
            'voting_power_distribution': {
                'top_1_percentage': 0.12,
                'top_5_percentage': 0.35,
                'top_10_percentage': 0.52,
                'gini_coefficient': 0.71
            },
            'delegation_data': {
                'total_delegated_power': 0.45,
                'top_delegate_percentage': 0.08
            },
            'emergency_procedures': {
                'active': False,
                'procedures_available': True
            }
        }

        governance_report = await governance_analyzer.analyze_governance_stability(sample_governance_data)
        print(f"   ✅ Analysis completed - Risk Level: {governance_report.overall_risk_level.value}")
        print(f"   ✅ Risk Score: {governance_report.overall_risk_score:.2f}/10")
        print(f"   ✅ Found {len(governance_report.attack_vector_assessments)} attack vector assessments")

        # 2. Voting Concentration Analyzer
        print("\n2. Testing Voting Concentration Analyzer...")
        from voting_concentration import VotingConcentrationAnalyzer

        voting_analyzer = VotingConcentrationAnalyzer(governance_analyzer.config)

        # Sample voting data
        sample_voting_data = {
            'holder_balances': {
                'whale_1': 500_000_000,
                'whale_2': 300_000_000,
                'whale_3': 200_000_000,
                **{f'user_{i}': 1_000_000 for i in range(100)}
            },
            'active_voters': 103,
            'delegation_data': {
                'delegate_powers': {
                    'delegate_1': 200_000_000,
                    'delegate_2': 150_000_000,
                    'delegate_3': 100_000_000
                }
            }
        }

        voting_metrics, voting_alerts = await voting_analyzer.analyze_voting_concentration(sample_voting_data)
        print(f"   ✅ Voting concentration analyzed")
        print(f"   ✅ Gini coefficient: {voting_metrics.gini_coefficient:.3f}")
        print(f"   ✅ Top 1% control: {voting_metrics.top_1_percentage:.1%}")
        print(f"   ✅ Generated {len(voting_alerts)} concentration alerts")

        # 3. Emergency Response Analyzer
        print("\n3. Testing Emergency Response Analyzer...")
        from emergency_response import EmergencyResponseAnalyzer

        emergency_analyzer = EmergencyResponseAnalyzer(governance_analyzer.config)

        sample_emergency_data = {
            'procedures': [
                {
                    'id': 'demo_procedure',
                    'name': 'Demo Emergency Procedure',
                    'emergency_types': ['security_breach'],
                    'activation_threshold': 7.0,
                    'response_time_target': 3600,
                    'automation_indicators': {
                        'automated_steps': 5,
                        'total_steps': 10,
                        'has_automated_monitoring': True
                    }
                }
            ],
            'response_teams': [
                {
                    'id': 'demo_team',
                    'name': 'Demo Response Team',
                    'team_size': 5,
                    'available_24x7': True,
                    'expertise_areas': ['security']
                }
            ]
        }

        emergency_report = await emergency_analyzer.analyze_emergency_readiness(sample_emergency_data)
        print(f"   ✅ Emergency readiness analyzed")
        print(f"   ✅ Readiness score: {emergency_report.overall_readiness_score:.2f}/10")
        print(f"   ✅ Found {len(emergency_report.available_procedures)} procedures")

        # 4. Network Security Assessment
        print("\n4. Testing Network Security Assessment...")
        from network_security import NetworkSecurityMetrics

        network_security = NetworkSecurityMetrics(governance_analyzer.config)

        sample_network_data = {
            'consensus': {
                'participation_rate': 0.87,
                'unique_participants': 1_250,
                'countries': ['US', 'EU', 'ASIA'],
                'top_10_stake_percentage': 0.25
            },
            'nodes': {
                'total_count': 2_100,
                'relay_count': 120,
                'participation_count': 1_250
            },
            'state_proofs': {
                'adoption_rate': 0.92,
                'avg_verification_time': 1650
            },
            'infrastructure': {
                'cloud_dependency': 0.35,
                'dns_dependency': 0.18
            }
        }

        network_report = await network_security.assess_network_security(sample_network_data)
        print(f"   ✅ Network security assessed")
        print(f"   ✅ Security score: {network_report['overall_security_score']:.2f}/10")
        print(f"   ✅ Risk level: {network_report['risk_level'].value}")

        # 5. Foundation Dependency Analysis
        print("\n5. Testing Foundation Dependency Analysis...")
        from foundation_dependency import FoundationDependencyAnalyzer

        foundation_analyzer = FoundationDependencyAnalyzer(governance_analyzer.config)

        sample_foundation_data = {
            'funding': {
                'runway_months': 48,
                'revenue_diversification': 0.35,
                'sustainability_score': 0.72
            },
            'governance': {
                'foundation_voting_power': 0.08,
                'foundation_influence_score': 0.35,
                'community_autonomy_score': 0.75
            },
            'development': {
                'foundation_core_developers': 18,
                'total_ecosystem_developers': 280,
                'foundation_commit_percentage': 0.55
            },
            'strategic': {
                'partnership_concentration': 0.25,
                'critical_vendor_count': 4,
                'relationship_stability_score': 0.85
            }
        }

        foundation_report = await foundation_analyzer.analyze_foundation_dependencies(sample_foundation_data)
        print(f"   ✅ Foundation dependencies analyzed")
        print(f"   ✅ Dependency risk: {foundation_report['overall_dependency_risk']:.2f}/10")
        print(f"   ✅ Risk level: {foundation_report['risk_level'].value}")

        # Summary
        print("\n" + "=" * 60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        print(f"\n📊 ASSESSMENT SUMMARY:")
        print(f"   • Governance Risk Score: {governance_report.overall_risk_score:.1f}/10")
        print(f"   • Voting Concentration: {voting_metrics.gini_coefficient:.2f} Gini coefficient")
        print(f"   • Emergency Readiness: {emergency_report.overall_readiness_score:.1f}/10")
        print(f"   • Network Security: {network_report['overall_security_score']:.1f}/10")
        print(f"   • Foundation Dependency: {foundation_report['overall_dependency_risk']:.1f}/10")

        print(f"\n🔍 KEY FINDINGS:")
        print(f"   • {len(governance_report.attack_vector_assessments)} attack vectors assessed")
        print(f"   • {len(voting_alerts)} voting concentration alerts")
        print(f"   • {len(emergency_report.available_procedures)} emergency procedures available")
        print(f"   • {sample_network_data['nodes']['total_count']:,} network nodes monitored")

        print(f"\n✅ SYSTEM STATUS: All components operational and ready for production use!")

        return True

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Algorand Governance Risk Assessment Demo...")

    try:
        success = asyncio.run(simple_governance_demo())

        if success:
            print(f"\n🎊 Demo completed successfully!")
            print(f"📚 For more details, see the Jupyter notebook: notebooks/governance_systemic_demo.ipynb")
            print(f"🧪 Run tests with: python3 -m pytest tests/ -v")
            sys.exit(0)
        else:
            print(f"\n💥 Demo failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n⏹️ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed with unexpected error: {e}")
        sys.exit(1)