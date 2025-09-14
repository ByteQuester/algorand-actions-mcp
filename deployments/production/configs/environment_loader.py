"""
Production Environment Loader
Loads configuration from external deployment directory
Maintains clean separation between source code and deployment configs
"""

import os
import sys
from pathlib import Path

def get_deployment_root():
    """Get the root deployment directory"""
    current_path = Path(__file__).resolve().parent
    # This file is in deployments/production/configs/
    deployment_root = current_path.parent.parent
    return deployment_root

def load_production_config():
    """Import production configuration from deployment directory"""
    deployment_root = get_deployment_root()
    configs_dir = deployment_root / "production" / "configs"

    # Add configs directory to Python path
    sys.path.insert(0, str(configs_dir))

    try:
        from production_config import ProductionConfig
        return ProductionConfig
    except ImportError as e:
        raise ImportError(f"Cannot load production config from {configs_dir}: {e}")

def load_production_loggers():
    """Import production logging from deployment directory"""
    deployment_root = get_deployment_root()
    configs_dir = deployment_root / "production" / "configs"

    # Add configs directory to Python path
    sys.path.insert(0, str(configs_dir))

    try:
        from production_logging import get_production_loggers
        return get_production_loggers()
    except ImportError as e:
        raise ImportError(f"Cannot load production logging from {configs_dir}: {e}")

def get_env_file_path():
    """Get path to production environment file"""
    deployment_root = get_deployment_root()
    return deployment_root / "production" / "configs" / ".env.production"