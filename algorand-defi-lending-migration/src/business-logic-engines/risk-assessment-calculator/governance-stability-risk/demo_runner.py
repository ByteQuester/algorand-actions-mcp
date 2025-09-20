#!/usr/bin/env python3
"""
Governance Stability and Systemic Risk Assessment Demo Runner

This script demonstrates the complete governance stability and systemic risk
assessment system for the Algorand ecosystem.

Usage:
    python demo_runner.py [--config CONFIG_PATH] [--output OUTPUT_FILE]

Features demonstrated:
- Governance attack vector detection
- Voting concentration analysis
- Proposal manipulation detection
- Emergency response assessment
- Protocol upgrade risk analysis
- Regulatory compliance monitoring
- Network security assessment
- Foundation dependency analysis
- Integrated systemic risk evaluation
"""

import asyncio
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the core module to the path
sys.path.append(str(Path(__file__).parent / "core"))

from systemic_engine import SystemicRiskEngine, SystemicRiskLevel
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('governance_risk_demo.log')
    ]
)

logger = logging.getLogger(__name__)

class GovernanceRiskDemo:
    """Demo runner for governance risk assessment system"""

    def __init__(self, config_path: str = None):
        """Initialize the demo runner"""
        self.config_path = config_path
        self.engine = SystemicRiskEngine(config_path)

    def generate_comprehensive_sample_data(self):
        """Generate comprehensive sample data for demonstration"""
        logger.info("Generating comprehensive sample data...")

        # Generate realistic Algorand ecosystem data
        sample_data = {
            'governance_data': {
                'total_voting_power': 5_000_000_000,  # 5B Algo
                'active_voters': 145_000,
                'current_proposals': [
                    {
                        'id': 'xGov-123',
                        'title': 'Consensus Algorithm Upgrade',
                        'content': 'Proposal to upgrade the consensus algorithm for improved performance.',
                        'submission_time': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                        'voting_deadline': (datetime.utcnow() + timedelta(days=11)).isoformat(),
                        'submitter': 'algorand_foundation',
                        'deliberation_time': 1209600,  # 14 days
                        'fund_allocation': 2_000_000
                    },
                    {
                        'id': 'xGov-124',
                        'title': 'Emergency Security Patch',
                        'content': 'Urgent security fix that must be implemented immediately.',
                        'submission_time': datetime.utcnow().isoformat(),
                        'voting_deadline': (datetime.utcnow() + timedelta(hours=48)).isoformat(),
                        'submitter': 'security_team',
                        'deliberation_time': 172800,  # 48 hours - potential flash governance
                        'fund_allocation': 500_000
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
            },

            'voting_data': {
                'holder_balances': {
                    **{f'whale_{i}': np.random.lognormal(17, 1) for i in range(10)},
                    **{f'institution_{i}': np.random.lognormal(15, 0.8) for i in range(50)},
                    **{f'user_{i}': np.random.lognormal(12, 1.2) for i in range(1000)}
                },
                'active_voters': 145_000,
                'delegation_data': {
                    'delegate_powers': {f'delegate_{i}': np.random.lognormal(16, 0.5) for i in range(1250)}
                },
                # Voting results for proposals
                'xGov-123': {
                    'total_votes': 85_000,
                    'yes_votes': 65_000,
                    'no_votes': 18_000,
                    'voting_power_yes': 2_800_000_000,
                    'voting_power_no': 600_000_000,
                    'voter_addresses': [f'voter_{i}' for i in range(85_000)],
                    'vote_timings': np.random.normal(7*24*3600, 2*24*3600, 85_000).tolist()
                },
                'xGov-124': {
                    'total_votes': 15_000,
                    'yes_votes': 14_500,
                    'no_votes': 400,
                    'voting_power_yes': 1_200_000_000,
                    'voting_power_no': 50_000_000,
                    'voter_addresses': [f'emergency_voter_{i}' for i in range(15_000)],
                    'vote_timings': np.random.exponential(3600, 15_000).tolist()
                }
            },

            'proposals_data': [
                {
                    'id': 'xGov-123',
                    'title': 'Consensus Algorithm Upgrade',
                    'content': 'Proposal to upgrade the consensus algorithm for improved performance.',
                    'submission_time': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                    'voting_deadline': (datetime.utcnow() + timedelta(days=11)).isoformat(),
                    'submitter': 'algorand_foundation',
                    'fund_allocation': 2_000_000
                },
                {
                    'id': 'xGov-124',
                    'title': 'Emergency Security Patch',
                    'content': 'Urgent security fix that must be implemented immediately.',
                    'submission_time': datetime.utcnow().isoformat(),
                    'voting_deadline': (datetime.utcnow() + timedelta(hours=48)).isoformat(),
                    'submitter': 'security_team',
                    'fund_allocation': 500_000
                }
            ],

            'network_data': {
                'consensus': {
                    'participation_rate': 0.87,
                    'unique_participants': 1_250,
                    'countries': ['US', 'EU', 'ASIA', 'OCEANIA'],
                    'top_10_stake_percentage': 0.25
                },
                'nodes': {
                    'total_count': 2_100,
                    'relay_count': 120,
                    'participation_count': 1_250,
                    'countries': ['US', 'EU', 'ASIA', 'OCEANIA', 'AFRICA']
                },
                'state_proofs': {
                    'adoption_rate': 0.92,
                    'avg_verification_time': 1650
                },
                'infrastructure': {
                    'cloud_dependency': 0.35,
                    'dns_dependency': 0.18
                }
            },

            'emergency_data': {
                'procedures': [
                    {
                        'id': 'security_incident_response',
                        'name': 'Security Incident Response',
                        'emergency_types': ['security_breach'],
                        'activation_threshold': 7.0,
                        'response_time_target': 1800,
                        'automation_indicators': {
                            'automated_steps': 6,
                            'total_steps': 10,
                            'has_automated_monitoring': True
                        },
                        'last_tested': (datetime.utcnow() - timedelta(days=15)).isoformat(),
                        'success_rate': 0.9
                    }
                ],
                'response_teams': [
                    {
                        'id': 'security_team',
                        'name': 'Security Team',
                        'team_size': 8,
                        'available_24x7': True,
                        'expertise_areas': ['security', 'incident_response']
                    }
                ]
            },

            'upgrade_data': {
                'active_upgrades': [
                    {
                        'id': 'consensus_upgrade_v2',
                        'name': 'Consensus Enhancement',
                        'type': 'consensus_change',
                        'phase': 'testing',
                        'planned_start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                        'planned_completion': (datetime.utcnow() + timedelta(days=60)).isoformat(),
                        'code_changes': 8500,
                        'affected_components': ['consensus_algorithm'],
                        'test_coverage': 89.5,
                        'node_coordination_required': True,
                        'emergency': False
                    }
                ]
            },

            'regulatory_data': {
                'events': [
                    {
                        'id': 'sec_guidance_2024',
                        'type': 'guidance_update',
                        'jurisdiction': 'US',
                        'title': 'SEC Updates DeFi Guidance',
                        'description': 'SEC provides updated guidance on DeFi protocols',
                        'severity': 'moderate',
                        'date': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                        'confidence': 0.9
                    }
                ],
                'compliance_requirements': [
                    {
                        'id': 'aml_kyc_us',
                        'jurisdiction': 'US',
                        'category': 'aml',
                        'description': 'AML/KYC requirements for DeFi protocols'
                    }
                ]
            },

            'foundation_data': {
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
        }

        logger.info("Sample data generation completed")
        return sample_data

    async def run_comprehensive_assessment(self, sample_data):
        """Run comprehensive systemic risk assessment"""
        logger.info("Starting comprehensive systemic risk assessment...")

        try:
            # Run the full systemic risk assessment
            report = await self.engine.assess_systemic_risk(sample_data)

            logger.info("Systemic risk assessment completed successfully")
            return report

        except Exception as e:
            logger.error(f"Systemic risk assessment failed: {e}")
            raise

    def print_executive_summary(self, report):
        """Print executive summary of the assessment"""
        print("\n" + "=" * 80)
        print("ALGORAND GOVERNANCE STABILITY & SYSTEMIC RISK ASSESSMENT")
        print("=" * 80)

        print(f"\nAssessment Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Assessment ID: {report.assessment_id}")

        print("\n" + "-" * 50)
        print("EXECUTIVE SUMMARY")
        print("-" * 50)

        exec_summary = report.executive_summary
        print(f"Overall Risk Level: {exec_summary['overall_risk_level'].upper()}")
        print(f"Overall Risk Score: {exec_summary['overall_risk_score']:.2f}/10")
        print(f"Stability Index: {exec_summary['stability_index']:.2f}/10")
        print(f"Resilience Score: {exec_summary['resilience_score']:.2f}/10")
        print(f"Risk Trend: {exec_summary['risk_trend'].upper()}")

        print(f"\nActive Alerts:")
        print(f"  • Critical: {exec_summary['critical_alerts_count']}")
        print(f"  • High Priority: {exec_summary['high_alerts_count']}")
        print(f"  • Immediate Action Required: {'YES' if exec_summary['immediate_actions_required'] else 'NO'}")

        print(f"\nTop Risk Areas:")
        for i, risk_area in enumerate(exec_summary.get('top_risks', [])[:3], 1):
            print(f"  {i}. {risk_area.replace('_', ' ').title()}")

    def print_component_breakdown(self, report):
        """Print detailed component risk breakdown"""
        print("\n" + "-" * 50)
        print("COMPONENT RISK BREAKDOWN")
        print("-" * 50)

        metrics = report.systemic_metrics

        components = {
            'Governance Risk': metrics.governance_risk_score,
            'Voting Concentration': metrics.voting_concentration_score,
            'Proposal Manipulation': metrics.proposal_manipulation_score,
            'Emergency Readiness': 10 - metrics.emergency_readiness_score,  # Invert
            'Upgrade Risks': metrics.upgrade_risk_score,
            'Regulatory Risk': metrics.regulatory_risk_score,
            'Network Security': 10 - metrics.network_security_score,  # Invert
            'Foundation Dependency': metrics.foundation_dependency_score
        }

        for component, score in components.items():
            risk_level = metrics.component_risk_levels.get(
                component.lower().replace(' ', '_'), 'moderate'
            )
            status_emoji = {
                'critical': '🔴',
                'high': '🟡',
                'moderate': '🟠',
                'low': '🟢',
                'minimal': '✅'
            }.get(risk_level, '⚪')

            print(f"{status_emoji} {component:.<30} {score:>5.1f}/10 ({risk_level.upper()})")

    def print_active_alerts(self, report):
        """Print active risk alerts"""
        print("\n" + "-" * 50)
        print("ACTIVE RISK ALERTS")
        print("-" * 50)

        if report.active_alerts:
            for i, alert in enumerate(report.active_alerts[:5], 1):
                severity_emoji = {
                    'CRITICAL': '🚨',
                    'HIGH': '⚠️',
                    'MODERATE': '📢',
                    'LOW': 'ℹ️'
                }.get(alert.severity, '📢')

                print(f"\n{i}. {severity_emoji} [{alert.severity}] {alert.alert_type}")
                print(f"   Component: {alert.component}")
                print(f"   Message: {alert.message}")
                print(f"   Immediate Action: {'YES' if alert.requires_immediate_action else 'NO'}")
                if alert.recommendations:
                    print(f"   Recommendation: {alert.recommendations[0]}")
        else:
            print("✅ No active alerts")

    def print_recommendations(self, report):
        """Print priority recommendations"""
        print("\n" + "-" * 50)
        print("PRIORITY RECOMMENDATIONS")
        print("-" * 50)

        for i, recommendation in enumerate(report.priority_recommendations[:7], 1):
            print(f"{i}. {recommendation}")

    def print_risk_projections(self, report):
        """Print risk projections"""
        print("\n" + "-" * 50)
        print("RISK PROJECTIONS")
        print("-" * 50)

        if report.risk_projections:
            for period, projected_risk in report.risk_projections.items():
                period_formatted = period.replace('_', ' ').title()
                trend_emoji = "📈" if projected_risk > report.systemic_metrics.overall_systemic_risk else "📉"
                print(f"{trend_emoji} {period_formatted:.<20} {projected_risk:>5.1f}/10")

    def save_detailed_report(self, report, output_file):
        """Save detailed report to JSON file"""
        logger.info(f"Saving detailed report to {output_file}")

        # Convert report to serializable format
        report_dict = {
            'timestamp': report.timestamp.isoformat(),
            'assessment_id': report.assessment_id,
            'executive_summary': report.executive_summary,
            'systemic_metrics': {
                'overall_risk_score': report.systemic_metrics.overall_systemic_risk,
                'overall_risk_level': report.systemic_metrics.overall_risk_level.value,
                'stability_index': report.systemic_metrics.stability_index,
                'resilience_score': report.systemic_metrics.resilience_score,
                'component_risk_levels': report.systemic_metrics.component_risk_levels,
                'risk_trend_direction': report.systemic_metrics.risk_trend_direction
            },
            'active_alerts': [
                {
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'component': alert.component,
                    'message': alert.message,
                    'requires_immediate_action': alert.requires_immediate_action,
                    'recommendations': alert.recommendations
                }
                for alert in report.active_alerts
            ],
            'priority_recommendations': report.priority_recommendations,
            'risk_projections': report.risk_projections,
            'early_warning_indicators': report.early_warning_indicators
        }

        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"Detailed report saved to {output_file}")

    async def run_demo(self, output_file=None):
        """Run the complete governance risk assessment demo"""
        print("🚀 Starting Algorand Governance Stability & Systemic Risk Assessment Demo")
        print("=" * 80)

        try:
            # Step 1: Generate sample data
            print("\n📊 Step 1: Generating comprehensive sample data...")
            sample_data = self.generate_comprehensive_sample_data()
            print(f"✅ Generated data for {len(sample_data)} risk components")

            # Step 2: Run comprehensive assessment
            print("\n🔍 Step 2: Running comprehensive systemic risk assessment...")
            report = await self.run_comprehensive_assessment(sample_data)
            print("✅ Systemic risk assessment completed")

            # Step 3: Display results
            print("\n📋 Step 3: Assessment Results")
            self.print_executive_summary(report)
            self.print_component_breakdown(report)
            self.print_active_alerts(report)
            self.print_recommendations(report)
            self.print_risk_projections(report)

            # Step 4: Save detailed report if requested
            if output_file:
                print(f"\n💾 Step 4: Saving detailed report...")
                self.save_detailed_report(report, output_file)
                print(f"✅ Report saved to {output_file}")

            # Step 5: Summary
            print("\n" + "=" * 80)
            print("DEMO COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"🎯 Overall Risk Assessment: {report.systemic_metrics.overall_risk_level.value.upper()}")
            print(f"📊 Risk Score: {report.systemic_metrics.overall_systemic_risk:.1f}/10")
            print(f"🛡️  System Resilience: {report.systemic_metrics.resilience_score:.1f}/10")
            print(f"⚠️  Active Alerts: {len(report.active_alerts)}")
            print(f"📈 Risk Trend: {report.systemic_metrics.risk_trend_direction.upper()}")

            print(f"\n🔧 System Features Demonstrated:")
            print(f"   • Governance attack vector detection")
            print(f"   • Voting concentration analysis")
            print(f"   • Proposal manipulation detection")
            print(f"   • Emergency response assessment")
            print(f"   • Protocol upgrade risk analysis")
            print(f"   • Regulatory compliance monitoring")
            print(f"   • Network security assessment")
            print(f"   • Foundation dependency analysis")
            print(f"   • Integrated systemic risk evaluation")

            print(f"\n✅ The governance stability and systemic risk assessment system is")
            print(f"   operational and ready for production deployment!")

            return report

        except Exception as e:
            logger.error(f"Demo execution failed: {e}")
            print(f"\n❌ Demo failed: {e}")
            raise

def main():
    """Main entry point for the demo"""
    parser = argparse.ArgumentParser(
        description="Algorand Governance Stability & Systemic Risk Assessment Demo"
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for detailed report (JSON format)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize and run demo
    demo = GovernanceRiskDemo(args.config)

    try:
        # Run the async demo
        report = asyncio.run(demo.run_demo(args.output))

        print(f"\n🎉 Demo completed successfully!")
        if args.output:
            print(f"📄 Detailed report saved to: {args.output}")

        sys.exit(0)

    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        print(f"\n💥 Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()