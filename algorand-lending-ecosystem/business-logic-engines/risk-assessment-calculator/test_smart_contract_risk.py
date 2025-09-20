"""
Test Smart Contract Risk Engine
Comprehensive tests for the smart contract security and interaction risk assessment engine
"""

import asyncio
import pytest
from datetime import datetime, timedelta
import yaml
from pathlib import Path

# Import the smart contract risk modules
from smart_contract_risk.core.contract_analyzer import SmartContractAnalyzer
from smart_contract_risk.core.interaction_risk import InteractionRiskAnalyzer
from smart_contract_risk.core.contract_engine import SmartContractRiskEngine

class TestSmartContractAnalyzer:
    """Test smart contract security analysis functionality"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return SmartContractAnalyzer()

    @pytest.fixture
    def sample_contract_data(self):
        """Sample contract data for testing"""
        return {
            'name': 'AlgoFi Lending Pool',
            'description': 'Main lending pool contract for AlgoFi protocol',
            'deployment_date': '2021-11-01',
            'functions': ['deposit', 'withdraw', 'borrow', 'repay', 'liquidate', 'external_call'],
            'features': ['access_control', 'reentrancy_protection', 'emergency_pause', 'event_logging'],
            'lines_of_code': 1200,
            'code_coverage': 0.85,
            'test_coverage': 0.78,
            'audits': [
                {
                    'auditor': 'runtime_verification',
                    'date': '2021-12-01',
                    'score': 88,
                    'type': 'formal_verification',
                    'vulnerabilities_found': 2,
                    'vulnerabilities_fixed': 2
                }
            ]
        }

    @pytest.fixture
    def risky_contract_data(self):
        """Risky contract data for testing"""
        return {
            'name': 'Unaudited Bridge Contract',
            'description': 'Cross-chain bridge with no audit',
            'deployment_date': '2023-01-01',
            'functions': ['lock', 'unlock', 'validate_proof', 'delegated_call'],
            'features': ['access_control'],  # Missing many security features
            'lines_of_code': 2000,
            'code_coverage': 0.45,
            'test_coverage': 0.30
            # No audits
        }

    @pytest.mark.asyncio
    async def test_contract_security_analysis(self, analyzer, sample_contract_data):
        """Test basic contract security analysis"""
        analysis = await analyzer.analyze_contract_security('test_contract', sample_contract_data)

        # Check basic structure
        assert analysis is not None
        assert analysis.contract_id == 'test_contract'
        assert analysis.contract_name == 'AlgoFi Lending Pool'
        assert analysis.contract_category == 'core_protocol'

        # Check security components
        assert len(analysis.audits) > 0
        assert analysis.vulnerability_assessment is not None
        assert analysis.contract_metrics is not None
        assert analysis.security_features is not None

        # Check scores
        assert 0 <= analysis.overall_security_score <= 1
        assert analysis.risk_tier in ['MINIMAL', 'LOW', 'MODERATE', 'GOOD', 'EXCELLENT']

    @pytest.mark.asyncio
    async def test_contract_category_determination(self, analyzer):
        """Test contract category determination"""
        # Test core protocol
        core_data = {'functions': ['deposit', 'withdraw', 'borrow']}
        analysis = await analyzer.analyze_contract_security('core_test', core_data)
        assert analysis.contract_category == 'core_protocol'

        # Test governance
        gov_data = {'functions': ['propose', 'vote', 'execute']}
        analysis = await analyzer.analyze_contract_security('gov_test', gov_data)
        assert analysis.contract_category == 'governance'

        # Test token
        token_data = {'functions': ['transfer', 'mint', 'burn']}
        analysis = await analyzer.analyze_contract_security('token_test', token_data)
        assert analysis.contract_category == 'token_contracts'

    @pytest.mark.asyncio
    async def test_audit_analysis(self, analyzer, sample_contract_data):
        """Test audit analysis functionality"""
        analysis = await analyzer.analyze_contract_security('test_contract', sample_contract_data)

        # Check audit processing
        assert len(analysis.audits) == 1
        audit = analysis.audits[0]

        assert audit.auditor == 'runtime_verification'
        assert audit.audit_score == 88
        assert audit.audit_type == 'formal_verification'
        assert audit.reputation_score == 95  # From config

    @pytest.mark.asyncio
    async def test_vulnerability_assessment(self, analyzer, risky_contract_data):
        """Test vulnerability assessment"""
        analysis = await analyzer.analyze_contract_security('risky_contract', risky_contract_data)

        vuln_assessment = analysis.vulnerability_assessment

        # Should detect vulnerabilities due to missing features and no audits
        assert vuln_assessment.total_score > 0
        assert vuln_assessment.risk_level in ['MODERATE', 'HIGH', 'CRITICAL']
        assert vuln_assessment.mitigation_status in ['UNAUDITED', 'CRITICAL_UNMITIGATED']

    @pytest.mark.asyncio
    async def test_security_features_analysis(self, analyzer, sample_contract_data):
        """Test security features analysis"""
        analysis = await analyzer.analyze_contract_security('test_contract', sample_contract_data)

        features = analysis.security_features

        # Check feature detection
        assert features.access_control == True
        assert features.reentrancy_protection == True
        assert features.emergency_pause == True
        assert features.event_logging == True

    @pytest.mark.asyncio
    async def test_contract_metrics_calculation(self, analyzer, sample_contract_data):
        """Test contract metrics calculation"""
        analysis = await analyzer.analyze_contract_security('test_contract', sample_contract_data)

        metrics = analysis.contract_metrics

        assert metrics.lines_of_code == 1200
        assert metrics.function_count == 6  # Number of functions
        assert 0 <= metrics.code_coverage <= 1
        assert 0 <= metrics.test_coverage <= 1

    @pytest.mark.asyncio
    async def test_batch_analysis(self, analyzer, sample_contract_data, risky_contract_data):
        """Test batch contract analysis"""
        contracts_data = {
            'safe_contract': sample_contract_data,
            'risky_contract': risky_contract_data
        }

        analyses = await analyzer.batch_analyze_contracts(contracts_data)

        assert len(analyses) == 2
        assert 'safe_contract' in analyses
        assert 'risky_contract' in analyses

        # Safe contract should have better security score
        assert analyses['safe_contract'].overall_security_score > analyses['risky_contract'].overall_security_score

    @pytest.mark.asyncio
    async def test_security_alerts(self, analyzer, risky_contract_data):
        """Test security alerts generation"""
        analyses = {'risky_contract': await analyzer.analyze_contract_security('risky_contract', risky_contract_data)}

        alerts = await analyzer.get_security_alerts(analyses)

        # Should generate alerts for risky contract
        assert len(alerts) > 0

        # Check alert structure
        for alert in alerts:
            assert alert['type'] is not None
            assert alert['severity'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            assert alert['message'] is not None

class TestInteractionRiskAnalyzer:
    """Test smart contract interaction risk analysis functionality"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return InteractionRiskAnalyzer()

    @pytest.fixture
    def sample_contracts_data(self):
        """Sample contracts data for testing"""
        return {
            'algofi_pool': {
                'name': 'AlgoFi Lending Pool',
                'functions': ['deposit', 'withdraw', 'borrow', 'repay', 'external_call'],
                'features': ['access_control', 'reentrancy_protection']
            },
            'tinyman_dex': {
                'name': 'Tinyman DEX',
                'functions': ['swap', 'add_liquidity', 'remove_liquidity', 'external_call'],
                'features': ['slippage_protection', 'access_control']
            },
            'oracle_contract': {
                'name': 'Price Oracle',
                'functions': ['update_price', 'get_price', 'validate_data'],
                'features': ['access_control', 'staleness_check']
            }
        }

    @pytest.fixture
    def sample_interaction_history(self):
        """Sample interaction history for testing"""
        return [
            {
                'source': 'algofi_pool',
                'target': 'oracle_contract',
                'type': 'price_query',
                'frequency': 150,
                'gas_usage': 25000,
                'success_rate': 0.98,
                'last_interaction': '2024-01-15T10:30:00'
            },
            {
                'source': 'tinyman_dex',
                'target': 'oracle_contract',
                'type': 'price_query',
                'frequency': 200,
                'gas_usage': 20000,
                'success_rate': 0.99,
                'last_interaction': '2024-01-15T10:25:00'
            }
        ]

    @pytest.mark.asyncio
    async def test_interaction_risk_analysis(self, analyzer, sample_contracts_data, sample_interaction_history):
        """Test basic interaction risk analysis"""
        assessment = await analyzer.analyze_interaction_risks(sample_contracts_data, sample_interaction_history)

        # Check basic structure
        assert assessment is not None
        assert len(assessment.contract_interactions) > 0
        assert len(assessment.interaction_patterns) > 0
        assert assessment.call_graph is not None

        # Check risk scores
        assert 0 <= assessment.overall_interaction_risk <= 1
        assert assessment.risk_level in ['MINIMAL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL']

    @pytest.mark.asyncio
    async def test_interaction_graph_building(self, analyzer, sample_contracts_data, sample_interaction_history):
        """Test interaction graph building"""
        assessment = await analyzer.analyze_interaction_risks(sample_contracts_data, sample_interaction_history)

        interactions = assessment.contract_interactions

        # Should have interactions from history plus inferred ones
        assert len(interactions) >= len(sample_interaction_history)

        # Check interaction structure
        for interaction in interactions:
            assert interaction.source_contract in sample_contracts_data
            assert interaction.target_contract in sample_contracts_data
            assert interaction.frequency > 0
            assert 0 <= interaction.risk_score <= 1

    @pytest.mark.asyncio
    async def test_interaction_pattern_detection(self, analyzer, sample_contracts_data, sample_interaction_history):
        """Test interaction pattern detection"""
        assessment = await analyzer.analyze_interaction_risks(sample_contracts_data, sample_interaction_history)

        patterns = assessment.interaction_patterns

        # Should detect patterns
        assert len(patterns) > 0

        # Check pattern structure
        for pattern in patterns:
            assert pattern.pattern_type is not None
            assert pattern.risk_level in ['LOW', 'MEDIUM', 'HIGH']
            assert len(pattern.contracts_involved) > 0
            assert len(pattern.vulnerability_indicators) >= 0

    @pytest.mark.asyncio
    async def test_call_graph_analysis(self, analyzer, sample_contracts_data, sample_interaction_history):
        """Test call graph analysis"""
        assessment = await analyzer.analyze_interaction_risks(sample_contracts_data, sample_interaction_history)

        call_graph = assessment.call_graph

        assert len(call_graph.nodes) == len(sample_contracts_data)
        assert len(call_graph.edges) > 0
        assert call_graph.max_call_depth >= 1
        assert 0 <= call_graph.complexity_score <= 1

    @pytest.mark.asyncio
    async def test_cross_protocol_risk_analysis(self, analyzer, sample_contracts_data):
        """Test cross-protocol risk analysis"""
        assessment = await analyzer.analyze_interaction_risks(sample_contracts_data)

        cross_protocol_risks = assessment.cross_protocol_risks

        # Should analyze cross-protocol interactions
        for protocol_pair, risk_score in cross_protocol_risks.items():
            assert 0 <= risk_score <= 1

    @pytest.mark.asyncio
    async def test_timing_attack_risk_analysis(self, analyzer, sample_contracts_data, sample_interaction_history):
        """Test timing attack risk analysis"""
        assessment = await analyzer.analyze_interaction_risks(sample_contracts_data, sample_interaction_history)

        timing_risks = assessment.timing_attack_risks

        # Should assess timing attack risks
        for interaction_key, risk_score in timing_risks.items():
            assert 0 <= risk_score <= 1

    @pytest.mark.asyncio
    async def test_front_running_risk_analysis(self, analyzer, sample_contracts_data, sample_interaction_history):
        """Test front-running risk analysis"""
        assessment = await analyzer.analyze_interaction_risks(sample_contracts_data, sample_interaction_history)

        front_running_risks = assessment.front_running_risks

        # Should assess front-running risks
        for interaction_key, risk_score in front_running_risks.items():
            assert 0 <= risk_score <= 1

class TestSmartContractRiskEngine:
    """Test the master smart contract risk engine"""

    @pytest.fixture
    def engine(self):
        """Create engine instance for testing"""
        return SmartContractRiskEngine()

    @pytest.fixture
    def sample_contracts_data(self):
        """Sample contracts data for testing"""
        return {
            'algofi_pool': {
                'name': 'AlgoFi Lending Pool',
                'functions': ['deposit', 'withdraw', 'borrow', 'repay', 'liquidate', 'external_call'],
                'features': ['access_control', 'reentrancy_protection', 'emergency_pause'],
                'deployment_date': '2021-11-01',
                'lines_of_code': 1200,
                'audits': [
                    {
                        'auditor': 'runtime_verification',
                        'date': '2021-12-01',
                        'score': 88,
                        'type': 'formal_verification',
                        'vulnerabilities_found': 2,
                        'vulnerabilities_fixed': 2
                    }
                ]
            },
            'tinyman_dex': {
                'name': 'Tinyman DEX',
                'functions': ['swap', 'add_liquidity', 'remove_liquidity', 'external_call'],
                'features': ['slippage_protection', 'access_control'],
                'deployment_date': '2021-10-01',
                'lines_of_code': 800
            },
            'oracle_contract': {
                'name': 'Price Oracle',
                'functions': ['update_price', 'get_price', 'validate_data'],
                'features': ['access_control', 'staleness_check'],
                'deployment_date': '2022-01-01',
                'lines_of_code': 400
            }
        }

    @pytest.fixture
    def sample_interaction_history(self):
        """Sample interaction history for testing"""
        return [
            {
                'source': 'algofi_pool',
                'target': 'oracle_contract',
                'type': 'price_query',
                'frequency': 150,
                'gas_usage': 25000,
                'success_rate': 0.98,
                'last_interaction': '2024-01-15T10:30:00'
            }
        ]

    @pytest.mark.asyncio
    async def test_comprehensive_assessment(self, engine, sample_contracts_data, sample_interaction_history):
        """Test comprehensive contract portfolio risk assessment"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data, sample_interaction_history)

        # Check main assessment structure
        assert assessment is not None
        assert assessment.portfolio_metrics is not None
        assert len(assessment.contract_scores) > 0
        assert len(assessment.contract_analyses) > 0
        assert assessment.interaction_assessment is not None

        # Check overall scores
        assert 0 <= assessment.overall_portfolio_risk <= 1
        assert assessment.risk_level in ['MINIMAL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL']
        assert 0 <= assessment.confidence_score <= 1

    @pytest.mark.asyncio
    async def test_portfolio_metrics_calculation(self, engine, sample_contracts_data):
        """Test portfolio metrics calculation"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)
        metrics = assessment.portfolio_metrics

        assert metrics.total_contracts == 3
        assert metrics.audited_contracts >= 0
        assert metrics.high_risk_contracts >= 0
        assert metrics.critical_vulnerabilities >= 0

    @pytest.mark.asyncio
    async def test_contract_risk_scores(self, engine, sample_contracts_data):
        """Test individual contract risk scores"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)

        assert len(assessment.contract_scores) == 3

        # Check contract score structure
        for score in assessment.contract_scores:
            assert score.contract_id in sample_contracts_data
            assert 0 <= score.security_score <= 1
            assert 0 <= score.audit_score <= 1
            assert 0 <= score.complexity_score <= 1
            assert 0 <= score.overall_risk_score <= 1
            assert score.risk_tier in ['MINIMAL', 'LOW', 'MODERATE', 'HIGH', 'CRITICAL']

    @pytest.mark.asyncio
    async def test_exploit_proximity_analysis(self, engine, sample_contracts_data):
        """Test exploit proximity analysis"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data, include_exploit_analysis=True)

        exploit_proximity = assessment.exploit_proximity_analysis

        # Should analyze exploit proximity for each contract
        for contract_id in sample_contracts_data.keys():
            assert contract_id in exploit_proximity
            assert 0 <= exploit_proximity[contract_id] <= 1

    @pytest.mark.asyncio
    async def test_upgrade_risk_analysis(self, engine, sample_contracts_data):
        """Test upgrade risk analysis"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)

        upgrade_risks = assessment.upgrade_risk_analysis

        # Should analyze upgrade risks
        for contract_id in sample_contracts_data.keys():
            assert contract_id in upgrade_risks
            assert 0 <= upgrade_risks[contract_id] <= 1

    @pytest.mark.asyncio
    async def test_admin_key_analysis(self, engine, sample_contracts_data):
        """Test admin key risk analysis"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)

        admin_key_risks = assessment.admin_key_analysis

        # Should analyze admin key risks
        for contract_id in sample_contracts_data.keys():
            assert contract_id in admin_key_risks
            assert 0 <= admin_key_risks[contract_id] <= 1

    @pytest.mark.asyncio
    async def test_dependency_risk_analysis(self, engine, sample_contracts_data, sample_interaction_history):
        """Test dependency risk analysis"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data, sample_interaction_history)

        dependency_risks = assessment.dependency_risk_analysis

        # Should analyze dependency risks
        for contract_id in sample_contracts_data.keys():
            assert contract_id in dependency_risks
            assert 0 <= dependency_risks[contract_id] <= 1

    @pytest.mark.asyncio
    async def test_risk_alerts_generation(self, engine, sample_contracts_data):
        """Test risk alerts generation"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)

        # Check alert structure
        for alert in assessment.risk_alerts:
            assert alert.alert_type is not None
            assert alert.severity in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            assert alert.message is not None
            assert alert.recommended_action is not None
            assert 1 <= alert.urgency_level <= 10

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, engine, sample_contracts_data):
        """Test recommendations generation"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)

        assert len(assessment.recommendations) > 0
        assert all(isinstance(rec, str) for rec in assessment.recommendations)

    @pytest.mark.asyncio
    async def test_monitoring_requirements(self, engine, sample_contracts_data):
        """Test monitoring requirements generation"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)

        assert len(assessment.monitoring_requirements) > 0
        assert all(isinstance(req, str) for req in assessment.monitoring_requirements)

    @pytest.mark.asyncio
    async def test_report_export(self, engine, sample_contracts_data):
        """Test assessment report export"""
        assessment = await engine.assess_contract_portfolio_risk(sample_contracts_data)

        # Export report
        report_path = await engine.export_assessment_report(assessment)

        # Check file exists and contains data
        assert Path(report_path).exists()

        # Read and validate JSON structure
        import json
        with open(report_path, 'r') as f:
            report_data = json.load(f)

        assert 'assessment_metadata' in report_data
        assert 'portfolio_metrics' in report_data
        assert 'contract_scores' in report_data

        # Cleanup
        Path(report_path).unlink()

class TestConfiguration:
    """Test configuration loading and validation"""

    def test_config_loading(self):
        """Test configuration file loading"""
        config_path = Path(__file__).parent / "smart-contract-risk" / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check main sections exist
        assert 'mcp_services' in config
        assert 'contract_risk_parameters' in config
        assert 'contract_categories' in config
        assert 'audit_database' in config

    def test_contract_categories_configuration(self):
        """Test contract categories configuration"""
        config_path = Path(__file__).parent / "smart-contract-risk" / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        categories = config['contract_categories']

        # Check major categories are configured
        assert 'core_protocol' in categories
        assert 'governance' in categories
        assert 'token_contracts' in categories
        assert 'oracle_integration' in categories

        # Check category structure
        for category_name, category_config in categories.items():
            assert 'description' in category_config
            assert 'base_risk_multiplier' in category_config
            assert 'critical_functions' in category_config

    def test_audit_database_configuration(self):
        """Test audit database configuration"""
        config_path = Path(__file__).parent / "smart-contract-risk" / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        audit_db = config['audit_database']

        # Check auditor configuration
        assert 'known_auditors' in audit_db
        auditors = audit_db['known_auditors']

        for auditor_name, auditor_config in auditors.items():
            assert 'reputation_score' in auditor_config
            assert 'specialization' in auditor_config

class TestRealWorldScenarios:
    """Test real-world scenarios and edge cases"""

    @pytest.fixture
    def engine(self):
        return SmartContractRiskEngine()

    @pytest.mark.asyncio
    async def test_high_security_portfolio(self, engine):
        """Test assessment of high-security portfolio"""
        secure_contracts = {
            'audited_protocol': {
                'name': 'Highly Audited Protocol',
                'functions': ['deposit', 'withdraw', 'borrow'],
                'features': [
                    'access_control', 'reentrancy_protection', 'emergency_pause',
                    'timelock_mechanism', 'multisig_requirement', 'input_validation'
                ],
                'lines_of_code': 800,
                'code_coverage': 0.95,
                'test_coverage': 0.90,
                'audits': [
                    {
                        'auditor': 'runtime_verification',
                        'date': '2023-06-01',
                        'score': 95,
                        'type': 'formal_verification',
                        'vulnerabilities_found': 0,
                        'vulnerabilities_fixed': 0
                    },
                    {
                        'auditor': 'certik',
                        'date': '2023-07-01',
                        'score': 92,
                        'type': 'security_audit',
                        'vulnerabilities_found': 1,
                        'vulnerabilities_fixed': 1
                    }
                ]
            }
        }

        assessment = await engine.assess_contract_portfolio_risk(secure_contracts)

        # Should have low risk scores
        assert assessment.overall_portfolio_risk < 0.3
        assert assessment.risk_level in ['MINIMAL', 'LOW']
        assert len([alert for alert in assessment.risk_alerts if alert.severity == 'CRITICAL']) == 0

    @pytest.mark.asyncio
    async def test_vulnerable_portfolio(self, engine):
        """Test assessment of vulnerable portfolio"""
        vulnerable_contracts = {
            'vulnerable_bridge': {
                'name': 'Vulnerable Bridge Contract',
                'functions': ['lock', 'unlock', 'validate_proof', 'delegated_call'],
                'features': [],  # No security features
                'lines_of_code': 2500,
                'code_coverage': 0.30,
                'test_coverage': 0.20
                # No audits
            },
            'complex_defi': {
                'name': 'Complex DeFi Protocol',
                'functions': [
                    'deposit', 'withdraw', 'borrow', 'liquidate', 'swap',
                    'add_liquidity', 'governance_vote', 'external_call'
                ],
                'features': ['access_control'],  # Minimal security
                'lines_of_code': 5000,
                'code_coverage': 0.50,
                'test_coverage': 0.40,
                'audits': [
                    {
                        'auditor': 'unknown_auditor',
                        'date': '2021-01-01',  # Very old audit
                        'score': 60,
                        'type': 'code_review',
                        'vulnerabilities_found': 15,
                        'vulnerabilities_fixed': 10
                    }
                ]
            }
        }

        assessment = await engine.assess_contract_portfolio_risk(vulnerable_contracts)

        # Should have high risk scores
        assert assessment.overall_portfolio_risk > 0.6
        assert assessment.risk_level in ['HIGH', 'CRITICAL']
        assert len(assessment.risk_alerts) > 0

    @pytest.mark.asyncio
    async def test_complex_interaction_patterns(self, engine):
        """Test assessment with complex interaction patterns"""
        contracts_data = {
            'protocol_a': {
                'name': 'Protocol A',
                'functions': ['deposit', 'withdraw', 'external_call'],
                'features': ['access_control']
            },
            'protocol_b': {
                'name': 'Protocol B',
                'functions': ['swap', 'external_call'],
                'features': ['access_control']
            },
            'protocol_c': {
                'name': 'Protocol C',
                'functions': ['bridge_transfer', 'external_call'],
                'features': ['access_control']
            }
        }

        # Complex interaction history with circular dependencies
        complex_interactions = [
            {
                'source': 'protocol_a',
                'target': 'protocol_b',
                'type': 'external_call',
                'frequency': 100,
                'gas_usage': 80000,
                'success_rate': 0.95
            },
            {
                'source': 'protocol_b',
                'target': 'protocol_c',
                'type': 'external_call',
                'frequency': 80,
                'gas_usage': 120000,
                'success_rate': 0.90
            },
            {
                'source': 'protocol_c',
                'target': 'protocol_a',
                'type': 'external_call',
                'frequency': 60,
                'gas_usage': 100000,
                'success_rate': 0.92
            }
        ]

        assessment = await engine.assess_contract_portfolio_risk(contracts_data, complex_interactions)

        # Should detect complex interaction risks
        assert assessment.interaction_assessment.overall_interaction_risk > 0.3
        assert len(assessment.interaction_assessment.call_graph.circular_dependencies) > 0

    @pytest.mark.asyncio
    async def test_empty_portfolio_handling(self, engine):
        """Test handling of empty portfolio"""
        with pytest.raises(ValueError):
            await engine.assess_contract_portfolio_risk({})

    @pytest.mark.asyncio
    async def test_single_contract_portfolio(self, engine):
        """Test assessment of single contract portfolio"""
        single_contract = {
            'only_contract': {
                'name': 'Single Contract',
                'functions': ['transfer', 'approve'],
                'features': ['access_control'],
                'lines_of_code': 200
            }
        }

        assessment = await engine.assess_contract_portfolio_risk(single_contract)

        assert assessment is not None
        assert len(assessment.contract_scores) == 1
        assert assessment.portfolio_metrics.total_contracts == 1

# Performance and stress tests
class TestPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def engine(self):
        return SmartContractRiskEngine()

    @pytest.mark.asyncio
    async def test_large_contract_portfolio_performance(self, engine):
        """Test performance with large contract portfolio"""
        # Create large portfolio
        large_contracts = {}
        for i in range(25):  # 25 contracts
            large_contracts[f'contract_{i}'] = {
                'name': f'Contract {i}',
                'functions': ['function_a', 'function_b', 'external_call'],
                'features': ['access_control'],
                'lines_of_code': 500 + (i * 50)
            }

        start_time = datetime.now()
        assessment = await engine.assess_contract_portfolio_risk(large_contracts)
        end_time = datetime.now()

        # Should complete within reasonable time (10 seconds)
        assert (end_time - start_time).total_seconds() < 10
        assert assessment is not None
        assert len(assessment.contract_scores) == 25

    @pytest.mark.asyncio
    async def test_complex_interaction_performance(self, engine):
        """Test performance with complex interaction patterns"""
        contracts_data = {f'contract_{i}': {
            'name': f'Contract {i}',
            'functions': ['function_a', 'external_call'],
            'features': ['access_control']
        } for i in range(10)}

        # Create many interactions
        interactions = []
        for i in range(10):
            for j in range(10):
                if i != j:
                    interactions.append({
                        'source': f'contract_{i}',
                        'target': f'contract_{j}',
                        'type': 'external_call',
                        'frequency': 50,
                        'gas_usage': 50000,
                        'success_rate': 0.95
                    })

        start_time = datetime.now()
        assessment = await engine.assess_contract_portfolio_risk(contracts_data, interactions)
        end_time = datetime.now()

        # Should complete within reasonable time
        assert (end_time - start_time).total_seconds() < 15
        assert assessment is not None

    @pytest.mark.asyncio
    async def test_concurrent_assessments(self, engine):
        """Test concurrent assessment performance"""
        contracts_list = [
            {f'contract_{i}': {
                'name': f'Contract {i}',
                'functions': ['function_a'],
                'features': ['access_control']
            }} for i in range(5)
        ]

        # Run concurrent assessments
        start_time = datetime.now()
        tasks = [engine.assess_contract_portfolio_risk(contracts) for contracts in contracts_list]
        assessments = await asyncio.gather(*tasks)
        end_time = datetime.now()

        # All should complete successfully
        assert len(assessments) == 5
        assert all(assessment is not None for assessment in assessments)

        # Should be reasonably fast
        assert (end_time - start_time).total_seconds() < 20

def run_tests():
    """Run all tests"""
    pytest.main([__file__, '-v', '-x'])

if __name__ == "__main__":
    run_tests()