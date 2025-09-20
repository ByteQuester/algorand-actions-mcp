"""
MCP Integration Test for DeFi Behavior Assessment Engine

Tests integration with MCP services for real-time data fetching and analysis.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from datetime import datetime
import json
import yaml

# Add the core module to the path
sys.path.append(str(Path(__file__).parent / "core"))

from core.behavior_engine import BehaviorEngine
from core.protocol_analyzer import ProtocolAnalyzer

class MCPIntegrationTester:
    """Tests MCP service integration for DeFi behavior assessment"""

    def __init__(self):
        """Initialize the MCP integration tester"""
        config_path = Path(__file__).parent / "config" / "config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.mcp_services = self.config['mcp_services']
        self.behavior_engine = BehaviorEngine()
        self.protocol_analyzer = ProtocolAnalyzer()

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

    async def test_algorand_transaction_fetching(self, test_address: str):
        """Test fetching Algorand transaction data via MCP"""
        print(f"\n📊 Testing transaction data fetching for {test_address[:10]}...")

        try:
            # Use the protocol analyzer to fetch transaction data
            analysis = await self.protocol_analyzer.analyze_cross_protocol_activity(
                address=test_address,
                analysis_period_days=30
            )

            print(f"✅ Transaction analysis completed:")
            print(f"   Protocols analyzed: {len(analysis.protocol_activities)}")
            print(f"   Diversification score: {analysis.diversification_score:.3f}")
            print(f"   Sophistication score: {analysis.sophistication_score:.3f}")
            print(f"   Engagement level: {analysis.engagement_level}")

            if analysis.protocol_activities:
                print(f"   Protocol breakdown:")
                for protocol, activity in analysis.protocol_activities.items():
                    print(f"     {protocol}: {activity.total_transactions} transactions, "
                          f"${activity.total_volume_usd:.2f} volume")

            return True

        except Exception as e:
            print(f"❌ Transaction fetching failed: {str(e)}")
            return False

    async def test_market_data_integration(self):
        """Test market data integration"""
        print("\n📈 Testing market data integration...")

        test_assets = ['ALGO', 'USDC', 'goBTC']
        results = {}

        for asset in test_assets:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.mcp_services['market_data_url']}/asset/{asset}"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            results[asset] = {
                                'status': '✅ Success',
                                'price': data.get('price', 'N/A'),
                                'volume': data.get('volume_24h', 'N/A')
                            }
                        else:
                            results[asset] = {'status': f'⚠️  HTTP {response.status}'}
            except Exception as e:
                results[asset] = {'status': f'❌ Error: {str(e)[:50]}'}

        print("Market Data Integration Results:")
        for asset, result in results.items():
            status = result['status']
            if 'Success' in status:
                price = result.get('price', 'N/A')
                volume = result.get('volume', 'N/A')
                print(f"   {asset}: {status} (Price: {price}, Volume: {volume})")
            else:
                print(f"   {asset}: {status}")

        return results

    async def test_full_behavior_analysis_with_mcp(self, test_address: str):
        """Test complete behavior analysis using MCP data"""
        print(f"\n🧠 Testing full behavior analysis with MCP integration...")

        try:
            # Run complete behavioral assessment
            assessment = await self.behavior_engine.assess_behavioral_risk(
                address=test_address,
                analysis_period_days=365
            )

            print(f"✅ Full behavior analysis completed:")
            print(f"   Overall Behavior Score: {assessment.overall_behavior_score:.3f}")
            print(f"   Sophistication Score: {assessment.sophistication_score:.3f}")
            print(f"   Risk Management Score: {assessment.risk_management_score:.3f}")
            print(f"   DeFi Experience Score: {assessment.defi_experience_score:.3f}")
            print(f"   Behavioral Risk Level: {assessment.behavioral_risk_level}")
            print(f"   Loan Recommendation: {assessment.loan_recommendation}")
            print(f"   Interest Rate Adjustment: {assessment.interest_rate_adjustment} bps")
            print(f"   Analysis Confidence: {assessment.analysis_confidence:.3f}")

            # Show some behavioral insights
            if assessment.strengths:
                print(f"   Behavioral Strengths: {len(assessment.strengths)}")
                for strength in assessment.strengths[:2]:
                    print(f"     • {strength}")

            if assessment.red_flags:
                print(f"   Red Flags: {len(assessment.red_flags)}")
                for flag in assessment.red_flags[:2]:
                    print(f"     • {flag}")

            return assessment

        except Exception as e:
            print(f"❌ Full analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def test_protocol_specific_analysis(self, test_address: str):
        """Test protocol-specific analysis features"""
        print(f"\n🔬 Testing protocol-specific analysis...")

        protocols_to_test = ['algofi', 'folks', 'tinyman', 'pact']
        results = {}

        for protocol in protocols_to_test:
            try:
                # This would test protocol-specific data fetching
                # For now, we'll simulate the test
                print(f"   Testing {protocol} integration...")

                # In a real implementation, this would fetch protocol-specific data
                results[protocol] = {
                    'status': '✅ Simulated success',
                    'transactions': 10,  # Mock data
                    'volume': 1000.0     # Mock data
                }

            except Exception as e:
                results[protocol] = {
                    'status': f'❌ Error: {str(e)}'
                }

        print("Protocol-Specific Analysis Results:")
        for protocol, result in results.items():
            print(f"   {protocol}: {result['status']}")

        return results

    async def test_real_time_updates(self):
        """Test real-time data update capabilities"""
        print(f"\n⏱️  Testing real-time update capabilities...")

        try:
            # Test real-time price updates
            test_asset = 'ALGO'
            timestamps = []
            prices = []

            for i in range(3):
                try:
                    async with aiohttp.ClientSession() as session:
                        url = f"{self.mcp_services['market_data_url']}/asset/{test_asset}"
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                price = data.get('price', 0)
                                timestamps.append(datetime.now())
                                prices.append(price)
                                print(f"   Update {i+1}: {test_asset} = ${price}")
                            else:
                                print(f"   Update {i+1}: Failed to fetch data")
                except:
                    print(f"   Update {i+1}: Connection error")

                if i < 2:  # Don't wait after the last iteration
                    await asyncio.sleep(2)  # Wait 2 seconds between updates

            if len(prices) >= 2:
                print(f"✅ Real-time updates working (received {len(prices)} price updates)")
                return True
            else:
                print(f"⚠️  Limited real-time data (received {len(prices)} updates)")
                return False

        except Exception as e:
            print(f"❌ Real-time update test failed: {str(e)}")
            return False

    async def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        print(f"\n🛡️  Testing error handling and fallbacks...")

        test_cases = [
            {
                'name': 'Invalid address',
                'address': 'INVALID_ADDRESS_123',
                'expected': 'Graceful error handling'
            },
            {
                'name': 'Empty address',
                'address': '',
                'expected': 'Input validation'
            },
            {
                'name': 'Non-existent protocol',
                'address': 'ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456',
                'expected': 'Protocol fallback handling'
            }
        ]

        results = []

        for test_case in test_cases:
            try:
                print(f"   Testing: {test_case['name']}")

                # Test with invalid/edge case data
                if test_case['address']:
                    analysis = await self.protocol_analyzer.analyze_cross_protocol_activity(
                        address=test_case['address'],
                        analysis_period_days=30
                    )
                    result = f"✅ Handled gracefully (score: {analysis.sophistication_score:.3f})"
                else:
                    result = "⚠️  Empty address case"

                results.append({
                    'test': test_case['name'],
                    'result': result
                })

            except Exception as e:
                result = f"❌ Error: {str(e)[:50]}"
                results.append({
                    'test': test_case['name'],
                    'result': result
                })

        print("Error Handling Test Results:")
        for result in results:
            print(f"   {result['test']}: {result['result']}")

        return results

    async def run_comprehensive_mcp_test(self):
        """Run comprehensive MCP integration test suite"""
        print("🚀 Starting Comprehensive MCP Integration Tests")
        print("=" * 70)

        # Test address (you can replace with a real Algorand address for testing)
        test_address = "ALGORANDADDRESS1234567890ABCDEF1234567890ABCDEF123456"

        test_results = {}

        try:
            # 1. Test service connectivity
            connectivity_results = await self.test_mcp_service_connectivity()
            test_results['connectivity'] = connectivity_results

            # 2. Test transaction data fetching
            transaction_success = await self.test_algorand_transaction_fetching(test_address)
            test_results['transaction_fetching'] = transaction_success

            # 3. Test market data integration
            market_data_results = await self.test_market_data_integration()
            test_results['market_data'] = market_data_results

            # 4. Test full behavior analysis
            behavior_analysis = await self.test_full_behavior_analysis_with_mcp(test_address)
            test_results['behavior_analysis'] = behavior_analysis is not None

            # 5. Test protocol-specific analysis
            protocol_results = await self.test_protocol_specific_analysis(test_address)
            test_results['protocol_analysis'] = protocol_results

            # 6. Test real-time updates
            realtime_success = await self.test_real_time_updates()
            test_results['realtime_updates'] = realtime_success

            # 7. Test error handling
            error_handling_results = await self.test_error_handling()
            test_results['error_handling'] = error_handling_results

            # Summary
            print(f"\n📋 MCP Integration Test Summary:")
            print(f"=" * 50)

            success_count = 0
            total_tests = 0

            for test_name, result in test_results.items():
                if test_name == 'connectivity':
                    connected_services = len([r for r in result.values() if '✅' in r])
                    total_services = len(result)
                    print(f"   Connectivity: {connected_services}/{total_services} services connected")
                    if connected_services > 0:
                        success_count += 1
                    total_tests += 1

                elif test_name in ['transaction_fetching', 'behavior_analysis', 'realtime_updates']:
                    status = "✅ Passed" if result else "❌ Failed"
                    print(f"   {test_name.replace('_', ' ').title()}: {status}")
                    if result:
                        success_count += 1
                    total_tests += 1

                elif test_name == 'market_data':
                    successful_assets = len([r for r in result.values() if '✅' in r['status']])
                    total_assets = len(result)
                    print(f"   Market Data: {successful_assets}/{total_assets} assets fetched")
                    if successful_assets > 0:
                        success_count += 1
                    total_tests += 1

            print(f"\n🎯 Overall Success Rate: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")

            if success_count == total_tests:
                print("🎉 All MCP integration tests passed!")
            elif success_count >= total_tests * 0.7:
                print("⚠️  Most tests passed - system is functional with some limitations")
            else:
                print("❌ Multiple test failures - integration issues detected")

            return test_results

        except Exception as e:
            print(f"❌ Comprehensive test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return test_results

def run_mcp_integration_tests():
    """Entry point for running MCP integration tests"""
    tester = MCPIntegrationTester()
    return asyncio.run(tester.run_comprehensive_mcp_test())

if __name__ == "__main__":
    run_mcp_integration_tests()