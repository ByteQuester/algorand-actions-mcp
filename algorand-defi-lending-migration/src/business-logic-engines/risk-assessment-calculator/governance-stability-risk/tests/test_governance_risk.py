"""
Comprehensive Test Suite for Governance Stability and Systemic Risk Assessment
Tests all components of the governance and systemic risk monitoring system
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the core module to the path
sys.path.append(str(Path(__file__).parent.parent / "core"))

from governance_analyzer import GovernanceAnalyzer, RiskLevel, AttackVector
from voting_concentration import VotingConcentrationAnalyzer, ConcentrationRiskLevel
from proposal_manipulation import ProposalManipulationDetector, ManipulationType
from emergency_response import EmergencyResponseAnalyzer, EmergencyType
from upgrade_risks import ProtocolUpgradeRiskAnalyzer, UpgradeRiskLevel
from regulatory_monitor import RegulatoryMonitor, RegulatoryEventType
from network_security import NetworkSecurityMetrics, SecurityRiskLevel
from foundation_dependency import FoundationDependencyAnalyzer, DependencyRiskLevel
from systemic_engine import SystemicRiskEngine, SystemicRiskLevel

class TestGovernanceStabilityRisk:
    """Test suite for governance stability and systemic risk components"""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            'governance_risk': {
                'voting_concentration': {
                    'critical_whale_threshold': 0.20,
                    'high_risk_threshold': 0.15,
                    'moderate_risk_threshold': 0.10
                },
                'proposal_risks': {
                    'flash_governance_window': 7200,
                    'minimum_deliberation_time': 172800
                }
            },
            'monitoring': {
                'intervals': {
                    'governance_check_seconds': 300
                },
                'alerts': {
                    'critical_risk_score': 8.0,
                    'high_risk_score': 6.0
                },
                'weights': {
                    'governance_weight': 0.25,
                    'regulatory_weight': 0.15,
                    'network_weight': 0.20,
                    'systemic_weight': 0.20
                }
            }
        }

    @pytest.fixture
    def sample_governance_data(self):
        """Sample governance data for testing"""
        return {
            'total_voting_power': 5_000_000_000,
            'active_voters': 145_000,
            'current_proposals': [
                {
                    'id': 'prop_001',
                    'title': 'Protocol Upgrade Proposal',
                    'submission_time': datetime.utcnow().isoformat(),
                    'voting_deadline': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                    'submitter': 'addr_123',
                    'deliberation_time': 86400
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
                'top_delegate_percentage': 0.08,
                'delegates_count': 1_250
            },
            'emergency_procedures': {
                'active': False,
                'procedures_available': True
            }
        }

    @pytest.fixture
    def sample_voting_data(self):
        """Sample voting data for testing"""
        return {
            'holder_balances': {
                'addr_1': 100_000_000,  # Large holder
                'addr_2': 50_000_000,   # Medium holder
                'addr_3': 25_000_000,   # Medium holder
                **{f'addr_{i}': 1_000_000 for i in range(4, 100)}  # Many small holders
            },
            'active_voters': 85,
            'delegation_data': {
                'delegate_powers': {
                    'delegate_1': 200_000_000,
                    'delegate_2': 150_000_000,
                    'delegate_3': 100_000_000
                }
            }
        }

    @pytest.fixture
    def sample_proposal_data(self):
        """Sample proposal data for testing"""
        return [
            {
                'id': 'prop_001',
                'title': 'Emergency Protocol Fix',
                'content': 'This is an urgent emergency fix that must be implemented immediately.',
                'submission_time': datetime.utcnow().isoformat(),
                'voting_deadline': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                'submitter': 'addr_emergency',
                'fund_allocation': 1_000_000,
                'affected_protocols': ['core_protocol']
            },
            {
                'id': 'prop_002',
                'title': 'Community Grant Proposal',
                'content': 'A comprehensive proposal for community development grants.',
                'submission_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'voting_deadline': (datetime.utcnow() + timedelta(days=14)).isoformat(),
                'submitter': 'addr_community',
                'fund_allocation': 500_000,
                'affected_protocols': ['grants_program']
            }
        ]

    @pytest.fixture
    def sample_voting_results(self):
        """Sample voting results for testing"""
        return {
            'prop_001': {
                'total_votes': 150,
                'yes_votes': 120,
                'no_votes': 25,
                'abstain_votes': 5,
                'voting_power_yes': 800_000_000,
                'voting_power_no': 200_000_000,
                'voter_addresses': [f'addr_{i}' for i in range(1, 151)],
                'vote_timings': [i * 100 for i in range(150)]  # Rapid voting pattern
            },
            'prop_002': {
                'total_votes': 500,
                'yes_votes': 300,
                'no_votes': 150,
                'abstain_votes': 50,
                'voting_power_yes': 1_200_000_000,
                'voting_power_no': 800_000_000,
                'voter_addresses': [f'addr_{i}' for i in range(1, 501)],
                'vote_timings': [i * 1000 for i in range(500)]  # Normal voting pattern
            }
        }

    @pytest.mark.asyncio
    async def test_governance_analyzer(self, sample_config, sample_governance_data):
        """Test governance stability analyzer"""
        analyzer = GovernanceAnalyzer()
        analyzer.config = sample_config

        report = await analyzer.analyze_governance_stability(sample_governance_data)

        assert report is not None
        assert hasattr(report, 'overall_risk_score')
        assert hasattr(report, 'overall_risk_level')
        assert isinstance(report.overall_risk_level, RiskLevel)
        assert len(report.attack_vector_assessments) > 0
        assert len(report.recommendations) > 0

        # Test specific attack vectors
        attack_types = {assessment.vector_type for assessment in report.attack_vector_assessments}
        assert AttackVector.FLASH_GOVERNANCE in attack_types
        assert AttackVector.WHALE_MANIPULATION in attack_types

    @pytest.mark.asyncio
    async def test_voting_concentration_analyzer(self, sample_config, sample_voting_data):
        """Test voting concentration analyzer"""
        analyzer = VotingConcentrationAnalyzer(sample_config)

        metrics, alerts = await analyzer.analyze_voting_concentration(sample_voting_data)

        assert metrics is not None
        assert hasattr(metrics, 'gini_coefficient')
        assert hasattr(metrics, 'top_1_percentage')
        assert 0 <= metrics.gini_coefficient <= 1
        assert 0 <= metrics.top_1_percentage <= 1

        # Test alert generation
        assert isinstance(alerts, list)
        if alerts:
            assert all(hasattr(alert, 'risk_level') for alert in alerts)

    @pytest.mark.asyncio
    async def test_proposal_manipulation_detector(self, sample_config, sample_proposal_data, sample_voting_results):
        """Test proposal manipulation detector"""
        detector = ProposalManipulationDetector(sample_config)

        report = await detector.analyze_proposal_manipulation(sample_proposal_data, sample_voting_results)

        assert report is not None
        assert hasattr(report, 'risk_score')
        assert hasattr(report, 'manipulation_indicators')
        assert len(report.manipulation_indicators) >= 0

        # Check for flash governance detection on emergency proposal
        flash_indicators = [
            indicator for indicator in report.manipulation_indicators
            if 'FLASH' in indicator.indicator_type
        ]
        assert len(flash_indicators) > 0  # Should detect emergency proposal as potential flash governance

    @pytest.mark.asyncio
    async def test_emergency_response_analyzer(self, sample_config):
        """Test emergency response analyzer"""
        analyzer = EmergencyResponseAnalyzer(sample_config)

        emergency_data = {
            'procedures': [
                {
                    'id': 'security_response',
                    'name': 'Security Incident Response',
                    'emergency_types': ['security_breach'],
                    'activation_threshold': 7.0,
                    'response_time_target': 1800,
                    'automation_indicators': {
                        'automated_steps': 5,
                        'total_steps': 10,
                        'has_automated_monitoring': True
                    }
                }
            ],
            'response_teams': [
                {
                    'id': 'security_team',
                    'name': 'Security Team',
                    'team_size': 5,
                    'available_24x7': True,
                    'expertise_areas': ['security', 'incident_response']
                }
            ]
        }

        report = await analyzer.analyze_emergency_readiness(emergency_data)

        assert report is not None
        assert hasattr(report, 'overall_readiness_score')
        assert 0 <= report.overall_readiness_score <= 10
        assert len(report.available_procedures) > 0
        assert len(report.response_teams) > 0

    @pytest.mark.asyncio
    async def test_upgrade_risk_analyzer(self, sample_config):
        """Test protocol upgrade risk analyzer"""
        analyzer = ProtocolUpgradeRiskAnalyzer(sample_config)

        upgrade_data = {
            'active_upgrades': [
                {
                    'id': 'upgrade_001',
                    'name': 'Consensus Improvement',
                    'type': 'consensus_change',
                    'phase': 'testing',
                    'planned_start': datetime.utcnow().isoformat(),
                    'planned_completion': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                    'code_changes': 5000,
                    'affected_components': ['consensus_algorithm', 'state_machine'],
                    'breaking_changes': True,
                    'test_coverage': 85.0,
                    'emergency': False
                }
            ]
        }

        report = await analyzer.assess_upgrade_risks(upgrade_data)

        assert report is not None
        assert hasattr(report, 'overall_risk_score')
        assert hasattr(report, 'risk_level')
        assert isinstance(report.risk_level, UpgradeRiskLevel)
        assert len(report.upgrade_metrics) > 0

    @pytest.mark.asyncio
    async def test_regulatory_monitor(self, sample_config):
        """Test regulatory monitor"""
        monitor = RegulatoryMonitor(sample_config)

        regulatory_data = {
            'events': [
                {
                    'id': 'reg_001',
                    'type': 'enforcement_action',
                    'jurisdiction': 'US',
                    'title': 'SEC Enforcement Action',
                    'description': 'SEC takes action against DeFi protocol for securities violations',
                    'severity': 'high',
                    'date': datetime.utcnow().isoformat(),
                    'confidence': 0.9,
                    'sources': ['sec.gov']
                }
            ],
            'compliance_requirements': [
                {
                    'id': 'comp_001',
                    'jurisdiction': 'US',
                    'category': 'aml',
                    'description': 'Anti-money laundering compliance requirements',
                    'scope': 'extensive'
                }
            ]
        }

        report = await monitor.monitor_regulatory_landscape(regulatory_data)

        assert report is not None
        assert hasattr(report, 'overall_risk_score')
        assert len(report.recent_events) > 0
        assert report.recent_events[0].event_type == RegulatoryEventType.ENFORCEMENT_ACTION

    @pytest.mark.asyncio
    async def test_network_security_metrics(self, sample_config):
        """Test network security metrics"""
        security = NetworkSecurityMetrics(sample_config)

        network_data = {
            'consensus': {
                'participation_rate': 0.85,
                'unique_participants': 1000,
                'countries': ['US', 'EU', 'ASIA', 'OCEANIA'],
                'top_10_stake_percentage': 0.25
            },
            'nodes': {
                'total_count': 2000,
                'relay_count': 120,
                'participation_count': 1000,
                'countries': ['US', 'EU', 'ASIA'],
                'cloud_concentration': 0.4
            },
            'state_proofs': {
                'adoption_rate': 0.9,
                'avg_verification_time': 1800
            },
            'infrastructure': {
                'cloud_dependency': 0.6,
                'dns_dependency': 0.2
            }
        }

        report = await security.assess_network_security(network_data)

        assert report is not None
        assert 'overall_security_score' in report
        assert 'risk_level' in report
        assert isinstance(report['risk_level'], SecurityRiskLevel)

    @pytest.mark.asyncio
    async def test_foundation_dependency_analyzer(self, sample_config):
        """Test foundation dependency analyzer"""
        analyzer = FoundationDependencyAnalyzer(sample_config)

        foundation_data = {
            'funding': {
                'runway_months': 36,
                'revenue_diversification': 0.3,
                'sustainability_score': 0.6
            },
            'governance': {
                'foundation_voting_power': 0.15,
                'foundation_influence_score': 0.4,
                'community_autonomy_score': 0.7
            },
            'development': {
                'foundation_core_developers': 15,
                'total_ecosystem_developers': 200,
                'foundation_commit_percentage': 0.6
            },
            'strategic': {
                'partnership_concentration': 0.3,
                'critical_vendor_count': 5,
                'relationship_stability_score': 0.8
            }
        }

        report = await analyzer.analyze_foundation_dependencies(foundation_data)

        assert report is not None
        assert 'overall_dependency_risk' in report
        assert 'risk_level' in report
        assert isinstance(report['risk_level'], DependencyRiskLevel)

    @pytest.mark.asyncio
    async def test_systemic_risk_engine(self, sample_config, sample_governance_data,
                                      sample_voting_data, sample_proposal_data, sample_voting_results):
        """Test the master systemic risk engine"""
        engine = SystemicRiskEngine()

        # Prepare comprehensive input data
        input_data = {
            'governance_data': sample_governance_data,
            'voting_data': sample_voting_data,
            'proposals_data': sample_proposal_data,
            'emergency_data': {
                'procedures': [],
                'response_teams': []
            },
            'upgrade_data': {
                'active_upgrades': []
            },
            'regulatory_data': {
                'events': [],
                'compliance_requirements': []
            },
            'network_data': {
                'consensus': {
                    'participation_rate': 0.85,
                    'unique_participants': 1000
                },
                'nodes': {
                    'total_count': 2000
                }
            },
            'foundation_data': {
                'funding': {
                    'runway_months': 36
                },
                'governance': {
                    'foundation_voting_power': 0.15
                }
            }
        }

        # Add voting results to voting data
        input_data['voting_data'].update(sample_voting_results)

        report = await engine.assess_systemic_risk(input_data)

        assert report is not None
        assert hasattr(report, 'systemic_metrics')
        assert hasattr(report, 'executive_summary')
        assert isinstance(report.systemic_metrics.overall_risk_level, SystemicRiskLevel)

        # Test executive summary
        assert 'overall_risk_level' in report.executive_summary
        assert 'overall_risk_score' in report.executive_summary
        assert 'top_recommendations' in report.executive_summary

        # Test that component reports are included
        assert report.governance_report is not None
        assert report.proposal_manipulation_report is not None

    def test_risk_level_mappings(self):
        """Test risk level enumeration mappings"""
        # Test that all risk level enums have proper values
        assert RiskLevel.CRITICAL.value == "critical"
        assert ConcentrationRiskLevel.HIGH.value == "high"
        assert UpgradeRiskLevel.MODERATE.value == "moderate"
        assert SecurityRiskLevel.LOW.value == "low"
        assert SystemicRiskLevel.CATASTROPHIC.value == "catastrophic"

    @pytest.mark.asyncio
    async def test_error_handling(self, sample_config):
        """Test error handling in various components"""
        analyzer = GovernanceAnalyzer()
        analyzer.config = sample_config

        # Test with invalid data
        try:
            report = await analyzer.analyze_governance_stability({})
            # Should handle gracefully and return default values
            assert report is not None
        except Exception as e:
            pytest.fail(f"Error handling failed: {e}")

    @pytest.mark.asyncio
    async def test_integration_workflow(self, sample_config, sample_governance_data):
        """Test integration workflow between components"""
        # Test that components can work together
        governance_analyzer = GovernanceAnalyzer()
        governance_analyzer.config = sample_config

        voting_analyzer = VotingConcentrationAnalyzer(sample_config)

        # Test governance analysis
        governance_report = await governance_analyzer.analyze_governance_stability(sample_governance_data)
        assert governance_report is not None

        # Test that governance data can be used for voting analysis
        voting_data = {
            'holder_balances': {f'addr_{i}': 1000000 for i in range(100)},
            'active_voters': 85
        }

        voting_metrics, alerts = await voting_analyzer.analyze_voting_concentration(voting_data)
        assert voting_metrics is not None

    def test_configuration_loading(self):
        """Test configuration loading and validation"""
        analyzer = GovernanceAnalyzer()

        # Test that default config is loaded
        assert analyzer.config is not None
        assert 'governance_risk' in analyzer.config
        assert 'monitoring' in analyzer.config

    @pytest.mark.asyncio
    async def test_real_time_monitoring(self, sample_config):
        """Test real-time monitoring capabilities"""
        engine = SystemicRiskEngine()

        # Test real-time status
        status = await engine.get_real_time_risk_status()
        assert 'status' in status

        # Test governance real-time alerts
        governance_analyzer = GovernanceAnalyzer()
        alerts = await governance_analyzer.get_real_time_alerts()
        assert isinstance(alerts, list)

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])