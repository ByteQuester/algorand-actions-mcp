#!/usr/bin/env python3
"""
Production Build Script for Lending Platform
Creates production-ready builds excluding development dependencies
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any

class ProductionBuilder:
    """Handles production build process"""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent.parent
        self.src_dir = self.base_dir / "src"
        self.build_dir = self.base_dir / "build"
        self.dist_dir = self.base_dir / "dist"

    def clean_build_dirs(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning build directories...")

        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed {dir_path}")

        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        print("✅ Build directories cleaned")

    def copy_source_code(self):
        """Copy production source code to build directory"""
        print("📦 Copying source code...")

        # Copy entire src directory
        shutil.copytree(self.src_dir, self.build_dir / "src")

        # Copy production configuration
        config_src = self.base_dir / "config"
        config_dst = self.build_dir / "config"
        shutil.copytree(config_src, config_dst)

        # Copy essential files
        essential_files = [
            "README.md",
            ".env.example"
        ]

        for file_name in essential_files:
            src_file = self.base_dir / file_name
            if src_file.exists():
                shutil.copy2(src_file, self.build_dir / file_name)

        print("✅ Source code copied")

    def create_production_requirements(self):
        """Create production requirements.txt excluding dev dependencies"""
        print("📋 Creating production requirements...")

        # Read base requirements
        base_requirements = self.src_dir / "agents" / "requirements.txt"

        production_requirements = []
        dev_keywords = ["test", "debug", "dev", "mock"]

        if base_requirements.exists():
            with open(base_requirements, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Skip development dependencies
                        if not any(keyword in line.lower() for keyword in dev_keywords):
                            production_requirements.append(line)

        # Add production-specific dependencies
        production_requirements.extend([
            "uvicorn>=0.20.0",
            "gunicorn>=20.1.0",
            "psycopg2-binary>=2.9.0",  # PostgreSQL driver
            "redis>=4.5.0",  # Caching
            "prometheus-client>=0.16.0",  # Metrics
        ])

        # Write production requirements
        req_file = self.build_dir / "requirements.txt"
        with open(req_file, 'w') as f:
            f.write("# Production Requirements for Lending Platform\n")
            f.write(f"# Generated on {self.get_timestamp()}\n\n")
            for req in sorted(production_requirements):
                f.write(f"{req}\n")

        print(f"✅ Production requirements created ({len(production_requirements)} packages)")

    def create_production_manifest(self):
        """Create production agent manifest"""
        print("🤖 Creating production manifest...")

        # Read source manifest
        src_manifest = self.src_dir / "agents" / "manifest.json"
        if not src_manifest.exists():
            print("❌ Source manifest not found")
            return

        with open(src_manifest, 'r') as f:
            manifest = json.load(f)

        # Update manifest for production
        manifest["deployment"]["production"]["built"] = True
        manifest["deployment"]["production"]["build_timestamp"] = self.get_timestamp()
        manifest["deployment"]["production"]["version"] = manifest.get("version", "1.0.0")

        # Remove development-specific configurations
        if "testing" in manifest:
            del manifest["testing"]["demo_scripts"]

        # Write production manifest
        prod_manifest = self.build_dir / "manifest.json"
        with open(prod_manifest, 'w') as f:
            json.dump(manifest, f, indent=2)

        print("✅ Production manifest created")

    def create_docker_files(self):
        """Create Docker configuration for production deployment"""
        print("🐳 Creating Docker configuration...")

        # Multi-stage Dockerfile
        dockerfile_content = '''# Production Dockerfile for Lending Platform
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash lending

# Copy installed packages from builder
COPY --from=builder /root/.local /home/lending/.local

# Set up application directory
WORKDIR /app
COPY --chown=lending:lending . .

# Create data directory
RUN mkdir -p /app/data && chown lending:lending /app/data

# Switch to non-root user
USER lending

# Set environment variables
ENV PATH=/home/lending/.local/bin:$PATH
ENV PYTHONPATH=/app/src
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD python scripts/deployment/health_check.py

# Expose port
EXPOSE 8003

# Start application
CMD ["python", "scripts/deployment/start_production.py"]
'''

        dockerfile_path = self.build_dir / "Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        # Docker compose for production
        docker_compose_content = '''version: '3.8'

services:
  lending-platform:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8003:8003"
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=INFO
      - LOG_FILE=true
    env_file:
      - config/production/.env.production
    volumes:
      - lending_data:/app/data
      - lending_logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "scripts/deployment/health_check.py"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: lending_platform
      POSTGRES_USER: lending_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/development/lending_database.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  lending_data:
  lending_logs:
  postgres_data:
  redis_data:
'''

        compose_path = self.build_dir / "docker-compose.production.yml"
        with open(compose_path, 'w') as f:
            f.write(docker_compose_content)

        print("✅ Docker configuration created")

    def create_startup_scripts(self):
        """Create production startup scripts"""
        print("🚀 Creating startup scripts...")

        # Health check script
        health_check_content = '''#!/usr/bin/env python3
"""
Health check script for production deployment
"""

import sys
import requests
import time
import os

def check_health():
    """Check application health"""
    try:
        port = os.getenv("PORT", "8003")
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
'''

        health_check_path = self.build_dir / "scripts" / "deployment" / "health_check.py"
        health_check_path.parent.mkdir(parents=True, exist_ok=True)
        with open(health_check_path, 'w') as f:
            f.write(health_check_content)
        health_check_path.chmod(0o755)

        # Production startup script
        startup_content = '''#!/usr/bin/env python3
"""
Production startup script for Lending Platform
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.logging_config import init_logging, get_logger

def start_production_server():
    """Start the production server"""
    # Initialize logging
    init_logging()
    logger = get_logger("lending.startup")

    logger.info("Starting Lending Platform in production mode...")

    # Environment checks
    required_env_vars = [
        "GOOGLE_API_KEY",
        "DATABASE_URL",
        "JWT_SECRET"
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Start server with Gunicorn
    port = os.getenv("PORT", "8003")
    host = os.getenv("HOST", "0.0.0.0")
    workers = os.getenv("WORKERS", "4")

    cmd = [
        "gunicorn",
        "--bind", f"{host}:{port}",
        "--workers", workers,
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--timeout", "120",
        "--keepalive", "5",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "--preload",
        "src.api.server:app"
    ]

    logger.info(f"Starting server: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_production_server()
'''

        startup_path = self.build_dir / "scripts" / "deployment" / "start_production.py"
        with open(startup_path, 'w') as f:
            f.write(startup_content)
        startup_path.chmod(0o755)

        print("✅ Startup scripts created")

    def create_deployment_guide(self):
        """Create deployment guide for production"""
        print("📖 Creating deployment guide...")

        guide_content = '''# Production Deployment Guide

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Environment variables** configured in `config/production/.env.production`
3. **Database** (PostgreSQL recommended for production)
4. **Google API key** with Gemini access

## Quick Deployment

### 1. Environment Setup

```bash
# Copy environment template
cp config/production/.env.production.template config/production/.env.production

# Edit with your production values
nano config/production/.env.production
```

### 2. Database Setup

```bash
# Start PostgreSQL
docker-compose -f docker-compose.production.yml up -d postgres

# Wait for database to be ready
sleep 30

# Run database migrations if needed
docker-compose -f docker-compose.production.yml exec postgres psql -U lending_user -d lending_platform -f /docker-entrypoint-initdb.d/init.sql
```

### 3. Start Application

```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs -f lending-platform
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:8003/health

# View status
docker-compose -f docker-compose.production.yml ps
```

## Monitoring

### Health Checks

The application provides health check endpoints:

- `/health` - Basic health status
- `/health/detailed` - Detailed system status

### Logging

Logs are structured JSON format in production:

```bash
# View application logs
docker-compose -f docker-compose.production.yml logs lending-platform

# Follow logs
docker-compose -f docker-compose.production.yml logs -f lending-platform
```

### Metrics

Prometheus metrics available at `/metrics` endpoint.

## Security Considerations

1. **Environment Variables**: Never commit `.env.production` to version control
2. **JWT Secret**: Use a secure, randomly generated secret key
3. **Database**: Use strong passwords and restrict access
4. **HTTPS**: Always use HTTPS in production
5. **Firewall**: Restrict access to necessary ports only

## Scaling

### Horizontal Scaling

```bash
# Scale application instances
docker-compose -f docker-compose.production.yml up -d --scale lending-platform=3
```

### Load Balancing

Add nginx or similar load balancer in front of application instances.

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.production.yml exec postgres pg_dump -U lending_user lending_platform > backup.sql

# Restore from backup
docker-compose -f docker-compose.production.yml exec -T postgres psql -U lending_user lending_platform < backup.sql
```

### Data Backup

```bash
# Backup application data
docker-compose -f docker-compose.production.yml exec lending-platform tar -czf /app/data/backup.tar.gz /app/data
```

## Troubleshooting

### Common Issues

1. **Database Connection**: Check DATABASE_URL and network connectivity
2. **Google API**: Verify GOOGLE_API_KEY is valid and has proper permissions
3. **MCP Services**: Ensure MCP endpoints are accessible
4. **Memory**: Monitor memory usage, increase if needed

### Debug Mode

```bash
# Enable debug logging temporarily
docker-compose -f docker-compose.production.yml exec lending-platform \
  env LOG_LEVEL=DEBUG python scripts/deployment/start_production.py
```

## Support

For issues or questions:
1. Check application logs
2. Verify configuration
3. Test MCP service connectivity
4. Review health check status
'''

        guide_path = self.build_dir / "DEPLOYMENT.md"
        with open(guide_path, 'w') as f:
            f.write(guide_content)

        print("✅ Deployment guide created")

    def create_distribution(self):
        """Create final distribution package"""
        print("📦 Creating distribution package...")

        # Create tar.gz distribution
        import tarfile

        dist_file = self.dist_dir / f"lending-platform-production-{self.get_timestamp()}.tar.gz"

        with tarfile.open(dist_file, "w:gz") as tar:
            tar.add(self.build_dir, arcname="lending-platform")

        print(f"✅ Distribution created: {dist_file}")
        return dist_file

    def get_timestamp(self) -> str:
        """Get current timestamp for versioning"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def build(self):
        """Execute complete build process"""
        print("🏗️  Starting production build process...")
        print(f"   Base directory: {self.base_dir}")
        print(f"   Source directory: {self.src_dir}")
        print(f"   Build directory: {self.build_dir}")
        print("")

        try:
            self.clean_build_dirs()
            self.copy_source_code()
            self.create_production_requirements()
            self.create_production_manifest()
            self.create_docker_files()
            self.create_startup_scripts()
            self.create_deployment_guide()
            dist_file = self.create_distribution()

            print("")
            print("🎉 Production build completed successfully!")
            print(f"   Distribution: {dist_file}")
            print(f"   Build directory: {self.build_dir}")
            print("")
            print("Next steps:")
            print("1. Review DEPLOYMENT.md for deployment instructions")
            print("2. Configure production environment variables")
            print("3. Deploy using Docker Compose")

        except Exception as e:
            print(f"❌ Build failed: {e}")
            sys.exit(1)

def main():
    """Main build script entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Build production distribution")
    parser.add_argument("--base-dir", help="Base directory (default: auto-detect)")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build directories")

    args = parser.parse_args()

    builder = ProductionBuilder(args.base_dir)

    if args.clean_only:
        builder.clean_build_dirs()
    else:
        builder.build()

if __name__ == "__main__":
    main()