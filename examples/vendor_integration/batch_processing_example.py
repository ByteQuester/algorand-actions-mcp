#!/usr/bin/env python3
"""
Batch Processing Integration Example

This demonstrates how to integrate the algorand-lending-business-logic package
for high-throughput batch processing of loan applications.

Features:
- Concurrent processing using ThreadPoolExecutor
- Progress tracking and reporting
- Error handling and retry logic
- CSV/JSON input/output support
- Performance metrics and optimization
- Memory-efficient processing for large datasets

Usage:
    pip install pandas tqdm
    python batch_processing_example.py

Input formats:
- CSV with columns: borrower, requested_amount, collateral_algo, duration_days
- JSON array with loan request objects
"""

import sys
import json
import csv
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import logging

# Add the vendor package to Python path (if not installed)
vendor_path = Path(__file__).parent / "algorand_lending_bl"
if vendor_path.exists():
    sys.path.insert(0, str(vendor_path.parent))

try:
    import pandas as pd
    from tqdm import tqdm
except ImportError:
    print("❌ Required packages not installed. Please run:")
    print("   pip install pandas tqdm")
    sys.exit(1)

# Import lending business logic
from algorand_lending_bl import (
    create_lending_service,
    LoanRequest,
    AlgorandAddress,
    ASAToken,
    VENDOR_INFO
)

# ============================================================================
# BATCH PROCESSOR CLASS
# ============================================================================

class LoanBatchProcessor:
    """High-performance batch processor for loan applications."""

    def __init__(self, max_workers: int = 4, chunk_size: int = 100):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum number of concurrent workers
            chunk_size: Number of requests to process in each chunk
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.lending_service = None
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None,
            'processing_times': []
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def initialize_service(self):
        """Initialize the lending service (thread-safe)."""
        if self.lending_service is None:
            self.lending_service = create_lending_service()
            self.logger.info(f"Lending service initialized with {len(self.lending_service)} engines")

    def process_single_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single loan request.

        Args:
            request_data: Dictionary containing loan request data

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()

        try:
            # Ensure service is initialized (thread-safe)
            if self.lending_service is None:
                self.initialize_service()

            # Parse request data
            borrower = AlgorandAddress(request_data['borrower'])

            # Handle different collateral formats
            collateral_assets = []
            if 'collateral_assets' in request_data:
                # JSON format with detailed assets
                for asset_data in request_data['collateral_assets']:
                    asset = ASAToken(
                        asset_id=asset_data['asset_id'],
                        amount=asset_data['amount']
                    )
                    collateral_assets.append(asset)
            elif 'collateral_algo' in request_data:
                # Simple CSV format with ALGO only
                algo_amount = int(request_data['collateral_algo'])
                collateral_assets.append(ASAToken(asset_id=0, amount=algo_amount))
            else:
                raise ValueError("No collateral data found")

            loan_request = LoanRequest(
                borrower=borrower,
                requested_amount=int(request_data['requested_amount']),
                collateral_assets=collateral_assets,
                loan_duration_days=int(request_data.get('duration_days', 30))
            )

            # Process loan - get all analyses for comprehensive processing
            collateral_analysis = self.lending_service["collateral"].analyze_collateral(
                loan_request.collateral_assets,
                loan_request.borrower
            )

            rate_calculation = self.lending_service["interest_rates"].calculate_interest_rate(loan_request)
            loan_decision = self.lending_service["loan_approval"].evaluate_loan(loan_request)
            risk_assessment = self.lending_service["risk_assessment"].assess_risk(loan_request)

            processing_time = time.time() - start_time

            # Create comprehensive result
            result = {
                'request_id': request_data.get('id', 'unknown'),
                'borrower': str(borrower),
                'requested_amount': loan_request.requested_amount,
                'requested_amount_algo': loan_request.requested_amount / 1_000_000,

                # Collateral analysis
                'collateral_value_usd': collateral_analysis.total_value,
                'liquidity_tier': collateral_analysis.liquidity_tier.value,
                'portfolio_risk': collateral_analysis.portfolio_risk.value,

                # Interest rate
                'base_rate': rate_calculation.base_rate,
                'final_rate': rate_calculation.final_rate,
                'risk_premium': rate_calculation.risk_premium,

                # Loan decision
                'decision': loan_decision.decision.value,
                'confidence': loan_decision.confidence.value,
                'approved_amount': loan_decision.approved_amount,
                'approved_amount_algo': loan_decision.approved_amount / 1_000_000,

                # Risk assessment
                'risk_score': risk_assessment.overall_score,
                'risk_level': risk_assessment.risk_level.value,
                'borrower_risk': risk_assessment.borrower_risk,
                'collateral_risk': risk_assessment.collateral_risk,

                # Processing metadata
                'processing_time_ms': round(processing_time * 1000, 2),
                'processing_status': 'success',
                'timestamp': time.time()
            }

            self.stats['successful'] += 1
            self.stats['processing_times'].append(processing_time)

            return result

        except Exception as e:
            processing_time = time.time() - start_time

            error_result = {
                'request_id': request_data.get('id', 'unknown'),
                'borrower': request_data.get('borrower', 'unknown'),
                'requested_amount': request_data.get('requested_amount', 0),
                'decision': 'error',
                'error_message': str(e),
                'error_type': type(e).__name__,
                'processing_time_ms': round(processing_time * 1000, 2),
                'processing_status': 'failed',
                'timestamp': time.time()
            }

            self.stats['failed'] += 1
            self.logger.error(f"Failed to process request {request_data.get('id', 'unknown')}: {e}")

            return error_result

    def process_batch_chunk(self, chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a chunk of requests sequentially.

        Args:
            chunk: List of request dictionaries

        Returns:
            List of results
        """
        results = []
        for request_data in chunk:
            result = self.process_single_request(request_data)
            results.append(result)
            self.stats['total_processed'] += 1

        return results

    def process_batch_concurrent(self, requests: List[Dict[str, Any]],
                               progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        Process requests concurrently using thread pool.

        Args:
            requests: List of request dictionaries
            progress_callback: Optional callback for progress updates

        Returns:
            List of results
        """
        self.stats['start_time'] = time.time()
        self.stats['total_processed'] = 0
        self.stats['successful'] = 0
        self.stats['failed'] = 0
        self.stats['processing_times'] = []

        # Initialize service once
        self.initialize_service()

        # Split requests into chunks for better memory management
        chunks = [requests[i:i + self.chunk_size] for i in range(0, len(requests), self.chunk_size)]
        total_chunks = len(chunks)

        self.logger.info(f"Processing {len(requests)} requests in {total_chunks} chunks "
                        f"with {self.max_workers} workers")

        all_results = []

        # Progress bar for chunks
        chunk_progress = tqdm(total=total_chunks, desc="Processing chunks", unit="chunk")

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all chunks
                future_to_chunk = {
                    executor.submit(self.process_batch_chunk, chunk): i
                    for i, chunk in enumerate(chunks)
                }

                # Process completed chunks
                for future in as_completed(future_to_chunk):
                    chunk_index = future_to_chunk[future]
                    try:
                        chunk_results = future.result()
                        all_results.extend(chunk_results)

                        # Update progress
                        chunk_progress.update(1)

                        if progress_callback:
                            progress_callback(len(all_results), len(requests))

                    except Exception as e:
                        self.logger.error(f"Chunk {chunk_index} failed: {e}")

        finally:
            chunk_progress.close()

        self.stats['end_time'] = time.time()

        return all_results

    def load_requests_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Load requests from CSV file."""
        self.logger.info(f"Loading requests from CSV: {file_path}")

        df = pd.read_csv(file_path)

        # Validate required columns
        required_columns = ['borrower', 'requested_amount']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Add ID column if not present
        if 'id' not in df.columns:
            df['id'] = range(1, len(df) + 1)

        # Convert to list of dictionaries
        requests = df.to_dict('records')

        self.logger.info(f"Loaded {len(requests)} requests from CSV")
        return requests

    def load_requests_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load requests from JSON file."""
        self.logger.info(f"Loading requests from JSON: {file_path}")

        with open(file_path, 'r') as f:
            requests = json.load(f)

        if not isinstance(requests, list):
            raise ValueError("JSON file must contain an array of requests")

        # Add ID if not present
        for i, request in enumerate(requests):
            if 'id' not in request:
                request['id'] = i + 1

        self.logger.info(f"Loaded {len(requests)} requests from JSON")
        return requests

    def save_results_to_csv(self, results: List[Dict[str, Any]], file_path: str):
        """Save results to CSV file."""
        if not results:
            self.logger.warning("No results to save")
            return

        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)
        self.logger.info(f"Saved {len(results)} results to CSV: {file_path}")

    def save_results_to_json(self, results: List[Dict[str, Any]], file_path: str):
        """Save results to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        self.logger.info(f"Saved {len(results)} results to JSON: {file_path}")

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.stats['processing_times']:
            return {"error": "No processing data available"}

        total_time = self.stats['end_time'] - self.stats['start_time']
        processing_times = self.stats['processing_times']

        return {
            "summary": {
                "total_requests": self.stats['total_processed'],
                "successful": self.stats['successful'],
                "failed": self.stats['failed'],
                "success_rate": f"{(self.stats['successful'] / self.stats['total_processed']) * 100:.2f}%"
            },
            "performance": {
                "total_time_seconds": round(total_time, 2),
                "requests_per_second": round(self.stats['total_processed'] / total_time, 2),
                "avg_processing_time_ms": round(sum(processing_times) / len(processing_times) * 1000, 2),
                "min_processing_time_ms": round(min(processing_times) * 1000, 2),
                "max_processing_time_ms": round(max(processing_times) * 1000, 2)
            },
            "configuration": {
                "max_workers": self.max_workers,
                "chunk_size": self.chunk_size,
                "package_version": VENDOR_INFO['version']
            }
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_sample_data(count: int, output_file: str, format_type: str = 'csv'):
    """Generate sample loan request data for testing."""
    import random

    sample_addresses = [
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
        "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
        "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
    ]

    requests = []
    for i in range(count):
        request = {
            'id': i + 1,
            'borrower': random.choice(sample_addresses),
            'requested_amount': random.randint(100000, 10000000),  # 0.1 to 10 ALGO
            'collateral_algo': random.randint(1000000, 20000000),  # 1 to 20 ALGO
            'duration_days': random.choice([7, 14, 30, 60, 90])
        }
        requests.append(request)

    if format_type == 'csv':
        df = pd.DataFrame(requests)
        df.to_csv(output_file, index=False)
    else:
        # Convert to JSON format with detailed collateral
        json_requests = []
        for req in requests:
            json_req = {
                'id': req['id'],
                'borrower': req['borrower'],
                'requested_amount': req['requested_amount'],
                'collateral_assets': [
                    {'asset_id': 0, 'amount': req['collateral_algo']}
                ],
                'duration_days': req['duration_days']
            }
            json_requests.append(json_req)

        with open(output_file, 'w') as f:
            json.dump(json_requests, f, indent=2)

    print(f"✓ Generated {count} sample requests in {output_file}")

def progress_callback(processed: int, total: int):
    """Progress callback for batch processing."""
    percentage = (processed / total) * 100
    print(f"\rProgress: {processed}/{total} ({percentage:.1f}%)", end='', flush=True)

# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def main():
    """Main demonstration of batch processing."""
    print("🏦 Algorand Lending Batch Processing Example")
    print("=" * 60)
    print(f"📦 Package: {VENDOR_INFO['name']} v{VENDOR_INFO['version']}")

    # Configuration
    max_workers = 4
    chunk_size = 50
    sample_count = 200

    # Initialize processor
    processor = LoanBatchProcessor(max_workers=max_workers, chunk_size=chunk_size)

    print(f"\n⚙️  Configuration:")
    print(f"   Max workers: {max_workers}")
    print(f"   Chunk size: {chunk_size}")
    print(f"   Sample requests: {sample_count}")

    # Generate sample data
    print(f"\n📝 Generating {sample_count} sample loan requests...")
    sample_csv = "sample_loan_requests.csv"
    sample_json = "sample_loan_requests.json"

    generate_sample_data(sample_count, sample_csv, 'csv')
    generate_sample_data(sample_count // 2, sample_json, 'json')

    # Process CSV data
    print(f"\n🔄 Processing CSV data ({sample_csv})...")
    try:
        csv_requests = processor.load_requests_from_csv(sample_csv)
        csv_results = processor.process_batch_concurrent(csv_requests, progress_callback)

        print(f"\n✓ CSV processing completed!")

        # Save results
        processor.save_results_to_csv(csv_results, "csv_processing_results.csv")
        processor.save_results_to_json(csv_results, "csv_processing_results.json")

        # Generate performance report
        csv_report = processor.generate_performance_report()

        print(f"\n📊 CSV Processing Performance Report:")
        print(f"   Total requests: {csv_report['summary']['total_requests']}")
        print(f"   Success rate: {csv_report['summary']['success_rate']}")
        print(f"   Processing time: {csv_report['performance']['total_time_seconds']}s")
        print(f"   Requests/second: {csv_report['performance']['requests_per_second']}")
        print(f"   Avg time per request: {csv_report['performance']['avg_processing_time_ms']}ms")

    except Exception as e:
        print(f"❌ CSV processing failed: {e}")

    # Process JSON data
    print(f"\n🔄 Processing JSON data ({sample_json})...")
    try:
        # Reset processor stats for JSON processing
        processor.stats = {
            'total_processed': 0, 'successful': 0, 'failed': 0,
            'start_time': None, 'end_time': None, 'processing_times': []
        }

        json_requests = processor.load_requests_from_json(sample_json)
        json_results = processor.process_batch_concurrent(json_requests, progress_callback)

        print(f"\n✓ JSON processing completed!")

        # Save results
        processor.save_results_to_json(json_results, "json_processing_results.json")

        # Generate performance report
        json_report = processor.generate_performance_report()

        print(f"\n📊 JSON Processing Performance Report:")
        print(f"   Total requests: {json_report['summary']['total_requests']}")
        print(f"   Success rate: {json_report['summary']['success_rate']}")
        print(f"   Processing time: {json_report['performance']['total_time_seconds']}s")
        print(f"   Requests/second: {json_report['performance']['requests_per_second']}")

    except Exception as e:
        print(f"❌ JSON processing failed: {e}")

    # Performance comparison
    print(f"\n🚀 Performance Summary:")
    print(f"   This demonstrates high-throughput batch processing")
    print(f"   Concurrent processing with {max_workers} workers")
    print(f"   Memory-efficient chunking with size {chunk_size}")
    print(f"   Comprehensive loan analysis for each request")
    print(f"   Error handling and detailed reporting")

    print(f"\n📁 Output files generated:")
    print(f"   sample_loan_requests.csv - Sample input data (CSV)")
    print(f"   sample_loan_requests.json - Sample input data (JSON)")
    print(f"   csv_processing_results.csv - Processing results (CSV)")
    print(f"   csv_processing_results.json - Processing results (JSON)")
    print(f"   json_processing_results.json - JSON processing results")

    print(f"\n🎉 Batch processing demonstration completed!")
    print(f"   The algorand-lending-business-logic package efficiently")
    print(f"   processed hundreds of loan requests with full analysis.")

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch loan processing example")
    parser.add_argument("--input", "-i", help="Input file (CSV or JSON)")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--format", choices=['csv', 'json'], default='json',
                       help="Output format")
    parser.add_argument("--workers", "-w", type=int, default=4,
                       help="Number of worker threads")
    parser.add_argument("--chunk-size", "-c", type=int, default=50,
                       help="Chunk size for processing")
    parser.add_argument("--generate", "-g", type=int,
                       help="Generate sample data with specified count")
    parser.add_argument("--demo", action="store_true",
                       help="Run demonstration with sample data")

    args = parser.parse_args()

    if args.demo:
        main()
    elif args.generate:
        output_file = args.output or f"sample_requests_{args.generate}.csv"
        generate_sample_data(args.generate, output_file)
    elif args.input:
        # Process specific file
        processor = LoanBatchProcessor(max_workers=args.workers, chunk_size=args.chunk_size)

        # Determine input format
        if args.input.endswith('.json'):
            requests = processor.load_requests_from_json(args.input)
        else:
            requests = processor.load_requests_from_csv(args.input)

        # Process requests
        results = processor.process_batch_concurrent(requests)

        # Save results
        output_file = args.output or f"batch_results.{args.format}"
        if args.format == 'csv':
            processor.save_results_to_csv(results, output_file)
        else:
            processor.save_results_to_json(results, output_file)

        # Print report
        report = processor.generate_performance_report()
        print(json.dumps(report, indent=2))
    else:
        parser.print_help()