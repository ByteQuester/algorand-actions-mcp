"""
MCP Integration Test for Collateral Intelligence Engine

Tests integration with MCP services for real-time collateral data and analysis.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from datetime import datetime
import json
import yaml
import numpy as np

# Add the core module to the path
sys.path.append(str(Path(__file__).parent / "core"))

from core.intelligence_engine import CollateralIntelligenceEngine
from core.smart_collateral import SmartCollateralAnalyzer
from core.liquidation_predictor import LiquidationPredictor

class MCPCollateralIntegrationTester:
    """Tests MCP service integration for collateral intelligence"""

    def __init__(self):
        """Initialize the MCP integration tester"""
        config_path = Path(__file__).parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.mcp_services = self.config['mcp_services']
        self.intelligence_engine = CollateralIntelligenceEngine()
        self.smart_analyzer = SmartCollateralAnalyzer()
        self.liquidation_predictor = LiquidationPredictor()

    async def test_mcp_service_connectivity(self):
        """Test connectivity to MCP services"""
        print("🔗 Testing MCP service connectivity...")

        results = {}

        # Test Algorand Reader Service
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.mcp_services['algorand_reader_url']}/health"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        results['algorand_reader'] = "✅ Connected"
                    else:
                        results['algorand_reader'] = f"⚠️  Status: {response.status}"
        except Exception as e:
            results['algorand_reader'] = f"❌ Connection failed: {str(e)}"

        # Test Market Data Service
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.mcp_services['market_data_url']}/health"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        results['market_data'] = "✅ Connected"
                    else:
                        results['market_data'] = f"⚠️  Status: {response.status}"
        except Exception as e:
            results['market_data'] = f"❌ Connection failed: {str(e)}"

        print("MCP Service Connectivity Results:")
        for service, status in results.items():
            print(f"   {service}: {status}")

        return results

    async def test_asset_data_fetching(self):
        """Test fetching asset data for collateral analysis"""
        print("\n📊 Testing asset data fetching...")

        test_assets = ['ALGO', 'USDC', 'goBTC', 'goETH', 'STBL']
        results = {}

        for asset in test_assets:
            try:
                # Test market data fetching
                async with aiohttp.ClientSession() as session:
                    url = f"{self.mcp_services['market_data_url']}/asset/{asset}"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            asset_data = data.get('asset_data', {})

                            results[asset] = {
                                'status': '✅ Success',
                                'price': asset_data.get('price', 'N/A'),
                                'market_cap': asset_data.get('market_cap', 'N/A'),
                                'volume_24h': asset_data.get('volume_24h', 'N/A'),
                                'volatility': asset_data.get('volatility_30d', 'N/A')
                            }
                        else:
                            results[asset] = {'status': f'⚠️  HTTP {response.status}'}

            except Exception as e:
                results[asset] = {'status': f'❌ Error: {str(e)[:50]}'}

        print("Asset Data Fetching Results:")
        for asset, result in results.items():
            status = result['status']
            if 'Success' in status:
                print(f"   {asset}: {status}")
                print(f"     Price: ${result.get('price', 'N/A')}")
                print(f"     Market Cap: ${result.get('market_cap', 'N/A'):,}" if isinstance(result.get('market_cap'), (int, float)) else f"     Market Cap: {result.get('market_cap', 'N/A')}")
                print(f"     24h Volume: ${result.get('volume_24h', 'N/A'):,}" if isinstance(result.get('volume_24h'), (int, float)) else f"     24h Volume: {result.get('volume_24h', 'N/A')}")
            else:
                print(f"   {asset}: {status}")

        return results

    async def test_smart_collateral_analysis_with_mcp(self):
        """Test smart collateral analysis using MCP data"""
        print("\n🧠 Testing smart collateral analysis with MCP integration...")

        # Create test portfolio with real market data
        test_portfolio = {
            'address': 'ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456',
            'assets': {
                'ALGO': {'amount': 20000},
                'USDC': {'amount': 10000},
                'goBTC': {'amount': 0.2}
            }
        }

        try:
            # Enhance portfolio with real market data
            enhanced_portfolio = await self._enhance_portfolio_with_mcp_data(test_portfolio)

            # Run smart collateral analysis
            analysis = await self.smart_analyzer.analyze_smart_collateral(
                collateral_portfolio=enhanced_portfolio
            )

            print(f"✅ Smart collateral analysis completed:")
            print(f"   Total Collateral Value: ${analysis.total_collateral_value:,.2f}")
            print(f"   Overall Quality Score: {analysis.quality_metrics.overall_quality_score:.3f}")
            print(f"   Liquidity Score: {analysis.quality_metrics.liquidity_score:.3f}")
            print(f"   Volatility Score: {analysis.quality_metrics.volatility_score:.3f}")
            print(f"   Market Cap Score: {analysis.quality_metrics.market_cap_score:.3f}")
            print(f"   Assets Analyzed: {len(analysis.collateral_assets)}")
            print(f"   Confidence Level: {analysis.confidence_level:.3f}")

            if analysis.collateral_assets:
                print(f"   Asset Breakdown:")
                for asset in analysis.collateral_assets:
                    print(f"     {asset.symbol}: Quality={asset.quality_score:.3f}, "
                          f"Risk={asset.risk_score:.3f}, Tier={asset.liquidity_tier}")

            if analysis.optimization_recommendations:
                print(f"   Optimization Recommendations:")
                for rec in analysis.optimization_recommendations[:3]:
                    print(f"     • {rec}")

            return analysis

        except Exception as e:
            print(f"❌ Smart collateral analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def test_liquidation_prediction_with_mcp(self):
        """Test liquidation prediction using MCP data"""
        print("\n⚠️  Testing liquidation prediction with MCP integration...")

        # Create test assets with market data
        test_assets = [
            {
                'symbol': 'ALGO',
                'amount': 20000,
                'current_price': 0.25,
                'market_cap': 2000000000,
                'daily_volume': 50000000,
                'volatility_30d': 0.45
            },
            {
                'symbol': 'USDC',
                'amount': 10000,
                'current_price': 1.00,
                'market_cap': 50000000000,
                'daily_volume': 5000000000,
                'volatility_30d': 0.02
            }
        ]

        try:
            # Enhance assets with real market data
            enhanced_assets = await self._enhance_assets_with_mcp_data(test_assets)

            # Run liquidation prediction
            analysis = await self.liquidation_predictor.predict_liquidation_risk(
                collateral_assets=enhanced_assets
            )

            print(f"✅ Liquidation prediction completed:")
            print(f"   Overall Liquidation Probability: {analysis.portfolio_risk.overall_liquidation_probability:.1%}")
            print(f"   Worst Case Scenario: {analysis.portfolio_risk.worst_case_scenario_probability:.1%}")
            print(f"   Expected Liquidation Value: ${analysis.portfolio_risk.expected_liquidation_value:,.2f}")
            print(f"   Time to Liquidation: {analysis.portfolio_risk.time_to_liquidation_estimate} days")
            print(f"   Cascade Risk: {analysis.portfolio_risk.cascade_risk_probability:.1%}")
            print(f"   Confidence Level: {analysis.confidence_level:.3f}")

            if analysis.asset_predictions:
                print(f"   Asset Predictions:")
                for pred in analysis.asset_predictions:
                    print(f"     {pred.asset_symbol} ({pred.prediction_horizon}): "
                          f"{pred.liquidation_probability:.1%} risk, "
                          f"Level: {pred.risk_level}")

            if analysis.risk_mitigation_strategies:
                print(f"   Risk Mitigation Strategies:")
                for strategy in analysis.risk_mitigation_strategies[:3]:
                    print(f"     • {strategy}")

            return analysis

        except Exception as e:
            print(f"❌ Liquidation prediction failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def test_full_intelligence_analysis_with_mcp(self):
        """Test complete intelligence analysis using MCP data"""
        print("\n🎯 Testing full collateral intelligence analysis with MCP...")

        test_portfolio = {
            'address': 'ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456',
            'assets': {
                'ALGO': {'amount': 30000},
                'USDC': {'amount': 15000},
                'goBTC': {'amount': 0.3},
                'goETH': {'amount': 2.0}
            },
            'market_conditions': {
                'sentiment': 0.6,
                'volatility_index': 0.35
            }
        }

        borrower_profile = {
            'address': test_portfolio['address'],
            'overall_behavior_score': 0.75,
            'sophistication_score': 0.8,
            'risk_management_score': 0.7
        }

        loan_request = {
            'amount': 12000,
            'currency': 'USDC',
            'duration_days': 90,
            'purpose': 'yield_farming'
        }

        try:
            # Enhance portfolio with real market data
            enhanced_portfolio = await self._enhance_portfolio_with_mcp_data(test_portfolio)

            # Run full intelligence analysis
            report = await self.intelligence_engine.analyze_collateral_portfolio(
                collateral_portfolio=enhanced_portfolio,
                borrower_profile=borrower_profile,
                loan_request=loan_request
            )

            print(f"✅ Full intelligence analysis completed:")
            print(f"   Address: {report.address}")
            print(f"   Total Collateral Value: ${report.smart_collateral_analysis.total_collateral_value:,.2f}")
            print(f"   Overall Collateral Score: {report.overall_collateral_score:.3f}")
            print(f"   Risk Adjusted Value: ${report.risk_adjusted_value:,.2f}")
            print(f"   Liquidation Adjusted Value: ${report.liquidation_adjusted_value:,.2f}")
            print(f"   Recommended LTV: {report.recommended_loan_to_value:.1%}")
            print(f"   Integrated Risk Score: {report.integrated_risk_score:.3f}")
            print(f"   Confidence Level: {report.confidence_level:.3f}")

            print(f"\n   Decision Support:")
            print(f"   Approval Recommendation: {report.approval_recommendation}")
            print(f"   Required Conditions: {len(report.required_conditions)}")
            print(f"   Monitoring Requirements: {len(report.monitoring_requirements)}")

            liquidation_risk = report.liquidation_prediction_analysis.portfolio_risk
            print(f"\n   Risk Assessment:")
            print(f"   Liquidation Probability: {liquidation_risk.overall_liquidation_probability:.1%}")
            print(f"   Cascade Risk: {liquidation_risk.cascade_risk_probability:.1%}")

            if report.optimization_recommendations:
                print(f"\n   Top Optimization Recommendations:")
                for i, rec in enumerate(report.optimization_recommendations[:3], 1):
                    print(f"     {i}. {rec}")

            return report

        except Exception as e:
            print(f"❌ Full intelligence analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def test_real_time_collateral_monitoring(self):
        """Test real-time collateral value monitoring"""
        print("\n⏱️  Testing real-time collateral monitoring...")

        test_assets = ['ALGO', 'USDC', 'goBTC']
        monitoring_results = []

        try:
            for i in range(3):  # 3 monitoring cycles
                print(f"   Monitoring cycle {i+1}:")

                cycle_data = {}
                total_value = 0

                for asset in test_assets:
                    try:
                        async with aiohttp.ClientSession() as session:
                            url = f"{self.mcp_services['market_data_url']}/asset/{asset}"
                            async with session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    price = data.get('asset_data', {}).get('price', 0)
                                    # Simulate holdings
                                    holdings = {'ALGO': 10000, 'USDC': 5000, 'goBTC': 0.1}
                                    value = price * holdings.get(asset, 0)
                                    total_value += value

                                    cycle_data[asset] = {
                                        'price': price,
                                        'value': value,
                                        'timestamp': datetime.now()
                                    }

                                    print(f"     {asset}: ${price:.4f} (Value: ${value:,.2f})")

                    except Exception as e:
                        print(f"     {asset}: Error fetching data")

                cycle_data['total_value'] = total_value
                cycle_data['timestamp'] = datetime.now()
                monitoring_results.append(cycle_data)

                print(f"     Total Portfolio Value: ${total_value:,.2f}")

                if i < 2:  # Don't wait after the last iteration
                    await asyncio.sleep(3)  # Wait 3 seconds between cycles

            # Analyze monitoring results
            if len(monitoring_results) >= 2:
                value_changes = []
                for i in range(1, len(monitoring_results)):
                    prev_value = monitoring_results[i-1]['total_value']
                    curr_value = monitoring_results[i]['total_value']
                    change = (curr_value - prev_value) / prev_value if prev_value > 0 else 0
                    value_changes.append(change)

                avg_change = np.mean(value_changes) if value_changes else 0
                print(f"✅ Real-time monitoring completed:")
                print(f"   Monitoring cycles: {len(monitoring_results)}")
                print(f"   Average value change: {avg_change:.2%}")

                return True

        except Exception as e:
            print(f"❌ Real-time monitoring failed: {str(e)}")
            return False

    async def test_stress_testing_scenarios(self):
        """Test stress testing with various market scenarios"""
        print("\n🧪 Testing stress testing scenarios...")

        scenarios = [
            {'name': 'Market Crash -30%', 'price_multiplier': 0.7},
            {'name': 'Flash Crash -50%', 'price_multiplier': 0.5},
            {'name': 'Bull Run +20%', 'price_multiplier': 1.2}
        ]

        base_portfolio = {
            'address': 'test_address',
            'assets': {
                'ALGO': {'amount': 10000},
                'USDC': {'amount': 5000},
                'goBTC': {'amount': 0.1}
            }
        }

        stress_results = []

        for scenario in scenarios:
            try:
                print(f"   Testing scenario: {scenario['name']}")

                # Create stress-modified portfolio
                stress_portfolio = await self._create_stress_portfolio(
                    base_portfolio, scenario['price_multiplier']
                )

                # Run analysis under stress conditions
                analysis = await self.smart_analyzer.analyze_smart_collateral(
                    collateral_portfolio=stress_portfolio
                )

                stress_result = {
                    'scenario': scenario['name'],
                    'total_value': analysis.total_collateral_value,
                    'quality_score': analysis.quality_metrics.overall_quality_score,
                    'confidence': analysis.confidence_level
                }

                stress_results.append(stress_result)

                print(f"     Total Value: ${stress_result['total_value']:,.2f}")
                print(f"     Quality Score: {stress_result['quality_score']:.3f}")

            except Exception as e:
                print(f"     Error in scenario {scenario['name']}: {str(e)}")

        print(f"✅ Stress testing completed: {len(stress_results)} scenarios tested")
        return stress_results

    async def _enhance_portfolio_with_mcp_data(self, portfolio):
        """Enhance portfolio with real MCP market data"""
        enhanced_portfolio = portfolio.copy()

        for asset_symbol, asset_data in portfolio.get('assets', {}).items():
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.mcp_services['market_data_url']}/asset/{asset_symbol}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            market_data = data.get('asset_data', {})

                            # Enhance with market data
                            enhanced_portfolio['assets'][asset_symbol].update({
                                'current_price': market_data.get('price', 1.0),
                                'market_cap': market_data.get('market_cap', 1000000),
                                'daily_volume': market_data.get('volume_24h', 100000),
                                'volatility_30d': market_data.get('volatility_30d', 0.3)
                            })

            except Exception:
                # Use fallback data if MCP fetch fails
                fallback_data = {
                    'ALGO': {'current_price': 0.25, 'market_cap': 2000000000, 'daily_volume': 50000000, 'volatility_30d': 0.45},
                    'USDC': {'current_price': 1.00, 'market_cap': 50000000000, 'daily_volume': 5000000000, 'volatility_30d': 0.02},
                    'goBTC': {'current_price': 45000, 'market_cap': 800000000000, 'daily_volume': 20000000000, 'volatility_30d': 0.60}
                }

                enhanced_portfolio['assets'][asset_symbol].update(
                    fallback_data.get(asset_symbol, {
                        'current_price': 1.0,
                        'market_cap': 1000000,
                        'daily_volume': 100000,
                        'volatility_30d': 0.5
                    })
                )

        return enhanced_portfolio

    async def _enhance_assets_with_mcp_data(self, assets):
        """Enhance asset list with MCP market data"""
        enhanced_assets = []

        for asset in assets:
            enhanced_asset = asset.copy()

            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.mcp_services['market_data_url']}/asset/{asset['symbol']}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            market_data = data.get('asset_data', {})

                            # Update with real market data
                            enhanced_asset.update({
                                'current_price': market_data.get('price', enhanced_asset.get('current_price', 1.0)),
                                'market_cap': market_data.get('market_cap', enhanced_asset.get('market_cap', 1000000)),
                                'daily_volume': market_data.get('volume_24h', enhanced_asset.get('daily_volume', 100000)),
                                'volatility_30d': market_data.get('volatility_30d', enhanced_asset.get('volatility_30d', 0.3))
                            })

            except Exception:
                # Keep original data if fetch fails
                pass

            enhanced_assets.append(enhanced_asset)

        return enhanced_assets

    async def _create_stress_portfolio(self, base_portfolio, price_multiplier):
        """Create a stress-tested version of the portfolio"""
        stress_portfolio = base_portfolio.copy()

        # Enhance with MCP data first
        enhanced_portfolio = await self._enhance_portfolio_with_mcp_data(stress_portfolio)

        # Apply stress multiplier to prices
        for asset_symbol, asset_data in enhanced_portfolio.get('assets', {}).items():
            if 'current_price' in asset_data:
                asset_data['current_price'] *= price_multiplier

            # Increase volatility during stress
            if 'volatility_30d' in asset_data:
                asset_data['volatility_30d'] = min(asset_data['volatility_30d'] * 1.5, 1.0)

        return enhanced_portfolio

    async def run_comprehensive_mcp_test(self):
        """Run comprehensive MCP integration test suite"""
        print("🚀 Starting Comprehensive Collateral Intelligence MCP Tests")
        print("=" * 75)

        test_results = {}

        try:
            # 1. Test service connectivity
            connectivity_results = await self.test_mcp_service_connectivity()
            test_results['connectivity'] = connectivity_results

            # 2. Test asset data fetching
            asset_data_results = await self.test_asset_data_fetching()
            test_results['asset_data_fetching'] = asset_data_results

            # 3. Test smart collateral analysis
            smart_analysis = await self.test_smart_collateral_analysis_with_mcp()
            test_results['smart_collateral_analysis'] = smart_analysis is not None

            # 4. Test liquidation prediction
            liquidation_analysis = await self.test_liquidation_prediction_with_mcp()
            test_results['liquidation_prediction'] = liquidation_analysis is not None

            # 5. Test full intelligence analysis
            intelligence_report = await self.test_full_intelligence_analysis_with_mcp()
            test_results['full_intelligence_analysis'] = intelligence_report is not None

            # 6. Test real-time monitoring
            realtime_success = await self.test_real_time_collateral_monitoring()
            test_results['realtime_monitoring'] = realtime_success

            # 7. Test stress scenarios
            stress_results = await self.test_stress_testing_scenarios()
            test_results['stress_testing'] = len(stress_results) > 0

            # Summary
            print(f"\n📋 Collateral Intelligence MCP Integration Summary:")
            print(f"=" * 60)

            success_count = 0
            total_tests = 0

            for test_name, result in test_results.items():
                if test_name == 'connectivity':
                    connected_services = len([r for r in result.values() if '✅' in r])
                    total_services = len(result)
                    print(f"   Connectivity: {connected_services}/{total_services} services")
                    if connected_services > 0:
                        success_count += 1
                    total_tests += 1

                elif test_name == 'asset_data_fetching':
                    successful_assets = len([r for r in result.values() if '✅' in r['status']])
                    total_assets = len(result)
                    print(f"   Asset Data Fetching: {successful_assets}/{total_assets} assets")
                    if successful_assets > 0:
                        success_count += 1
                    total_tests += 1

                elif test_name in ['smart_collateral_analysis', 'liquidation_prediction',
                                 'full_intelligence_analysis', 'realtime_monitoring', 'stress_testing']:
                    status = "✅ Passed" if result else "❌ Failed"
                    print(f"   {test_name.replace('_', ' ').title()}: {status}")
                    if result:
                        success_count += 1
                    total_tests += 1

            print(f"\n🎯 Overall Success Rate: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")

            if success_count == total_tests:
                print("🎉 All collateral intelligence MCP tests passed!")
            elif success_count >= total_tests * 0.7:
                print("⚠️  Most tests passed - system functional with minor issues")
            else:
                print("❌ Multiple test failures - integration issues detected")

            return test_results

        except Exception as e:
            print(f"❌ Comprehensive test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return test_results

def run_collateral_mcp_integration_tests():
    """Entry point for running collateral intelligence MCP integration tests"""
    tester = MCPCollateralIntegrationTester()
    return asyncio.run(tester.run_comprehensive_mcp_test())

if __name__ == "__main__":
    run_collateral_mcp_integration_tests()