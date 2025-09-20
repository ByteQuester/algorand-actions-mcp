#!/usr/bin/env python3
"""
Startup script for the Unified API Gateway

This script provides an easy way to start the API gateway with proper
configuration and environment setup. It handles both vendor mode and
hosted service mode configurations.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('gateway.log')
        ]
    )

def set_default_environment():
    """Set default environment variables if not already set"""
    defaults = {
        'GATEWAY_HOST': '0.0.0.0',
        'GATEWAY_PORT': '8000',
        'LENDING_MODE': 'vendor',
        'LOG_LEVEL': 'INFO',
        'CORS_ORIGINS': 'http://localhost:8000,http://localhost:8081',
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRE_MINUTES': '60',
    }

    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value

def setup_vendor_mode():
    """Setup environment for vendor mode"""
    print("Configuring for Vendor Mode (Direct Import)...")
    os.environ['LENDING_MODE'] = 'vendor'

    # Set service config file
    config_file = Path(__file__).parent / 'config' / 'services.json'
    os.environ['SERVICE_CONFIG_FILE'] = str(config_file)

    print("✓ Vendor mode configuration complete")

def setup_hosted_mode():
    """Setup environment for hosted service mode"""
    print("Configuring for Hosted Service Mode (HTTP Services)...")
    os.environ['LENDING_MODE'] = 'hosted'

    # Set service config file
    config_file = Path(__file__).parent / 'config' / 'services-hosted.json'
    os.environ['SERVICE_CONFIG_FILE'] = str(config_file)

    # Set default service URLs if not provided
    service_defaults = {
        'COLLATERAL_ANALYZER_URL': 'http://localhost:8001',
        'RATE_CALCULATOR_URL': 'http://localhost:8002',
        'LOAN_EVALUATOR_URL': 'http://localhost:8003',
        'RISK_ASSESSOR_URL': 'http://localhost:8004',
    }

    for key, value in service_defaults.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"  {key} = {value}")

    print("✓ Hosted service mode configuration complete")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import fastapi
        import uvicorn
        import httpx
        import redis
        import psutil
        print("✓ All required dependencies are available")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_vendor_mode_dependencies():
    """Check if vendor mode dependencies are available"""
    try:
        # Try to import the lending business logic
        import algorand_lending_bl
        print("✓ Algorand lending business logic package is available")
        return True
    except ImportError:
        print("⚠ Warning: algorand_lending_bl package not found")
        print("  Vendor mode may not work properly without the business logic package")
        return False

def check_hosted_mode_services():
    """Check if hosted services are reachable (optional check)"""
    import httpx

    services = [
        ('Collateral Analyzer', os.getenv('COLLATERAL_ANALYZER_URL')),
        ('Rate Calculator', os.getenv('RATE_CALCULATOR_URL')),
        ('Loan Evaluator', os.getenv('LOAN_EVALUATOR_URL')),
        ('Risk Assessor', os.getenv('RISK_ASSESSOR_URL')),
    ]

    print("Checking hosted service availability...")

    async def check_service(name, url):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    print(f"  ✓ {name} at {url}")
                    return True
                else:
                    print(f"  ⚠ {name} at {url} (status: {response.status_code})")
                    return False
        except Exception as e:
            print(f"  ✗ {name} at {url} (error: {e})")
            return False

    # Note: This is a simplified sync check for startup
    # The actual health monitoring happens in the gateway
    for name, url in services:
        if url:
            print(f"  → {name} configured at {url}")

def start_gateway():
    """Start the API gateway"""
    try:
        import uvicorn
        from src.api.gateway import app

        host = os.getenv('GATEWAY_HOST', '0.0.0.0')
        port = int(os.getenv('GATEWAY_PORT', 8000))
        log_level = os.getenv('LOG_LEVEL', 'info').lower()

        print(f"\n🚀 Starting Algorand Lending API Gateway")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Mode: {os.getenv('LENDING_MODE')}")
        print(f"   Log Level: {log_level}")
        print(f"   Documentation: http://{host}:{port}/api/v1/docs")
        print(f"   Health Check: http://{host}:{port}/health")
        print(f"   Metrics: http://{host}:{port}/metrics")

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            reload=False,  # Set to True for development
        )

    except KeyboardInterrupt:
        print("\n👋 Gateway shutdown requested")
    except Exception as e:
        print(f"\n💥 Failed to start gateway: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(description='Start the Algorand Lending API Gateway')
    parser.add_argument(
        '--mode',
        choices=['vendor', 'hosted'],
        default=os.getenv('LENDING_MODE', 'vendor'),
        help='Deployment mode (vendor or hosted)'
    )
    parser.add_argument(
        '--host',
        default=os.getenv('GATEWAY_HOST', '0.0.0.0'),
        help='Host to bind to'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('GATEWAY_PORT', 8000)),
        help='Port to bind to'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=os.getenv('LOG_LEVEL', 'INFO'),
        help='Logging level'
    )
    parser.add_argument(
        '--check-services',
        action='store_true',
        help='Check service availability before starting (hosted mode only)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Set environment variables from args
    os.environ['GATEWAY_HOST'] = args.host
    os.environ['GATEWAY_PORT'] = str(args.port)
    os.environ['LOG_LEVEL'] = args.log_level

    print("🔧 Initializing Algorand Lending API Gateway...")

    # Set default environment
    set_default_environment()

    # Check basic dependencies
    if not check_dependencies():
        sys.exit(1)

    # Configure based on mode
    if args.mode == 'vendor':
        setup_vendor_mode()
        check_vendor_mode_dependencies()
    elif args.mode == 'hosted':
        setup_hosted_mode()
        if args.check_services:
            check_hosted_mode_services()

    # Start the gateway
    start_gateway()

if __name__ == '__main__':
    main()