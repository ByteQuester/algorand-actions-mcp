# Makefile for Algorand MCP Workers
# Provides convenient commands for development and deployment

.PHONY: help install build docker-build docker-test docker-up docker-down clean

# Default target
help: ## Show this help message
	@echo "Algorand MCP Workers - Development Commands"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
install: ## Install dependencies
	pnpm install --frozen-lockfile

build: ## Build all packages
	pnpm --filter "@algorand-showcase/*" run build

dev-setup: ## Setup development environment
	@chmod +x scripts/dev-setup.sh
	@scripts/dev-setup.sh

# Docker commands
docker-build: ## Build Docker images
	@chmod +x scripts/build-docker.sh
	@scripts/build-docker.sh

docker-test: ## Test Docker containers
	@chmod +x scripts/test-containers.sh
	@scripts/test-containers.sh

docker-up: ## Start all services
	docker compose up

docker-up-d: ## Start all services in background
	docker compose up -d

docker-up-actions: ## Start only Actions MCP Worker
	docker compose up actions-mcp

docker-up-remote: ## Start only Remote MCP Worker
	docker compose up remote-mcp

docker-down: ## Stop all services
	docker compose down

docker-logs: ## View logs
	docker compose logs -f

docker-clean: ## Clean Docker resources
	docker compose down -v --remove-orphans
	docker system prune -f

# Monitoring
monitor-up: ## Start with monitoring stack
	docker compose --profile monitoring up -d

monitor-down: ## Stop monitoring stack
	docker compose --profile monitoring down

# Proxy
proxy-up: ## Start with Traefik proxy
	docker compose --profile proxy up -d

proxy-down: ## Stop Traefik proxy
	docker compose --profile proxy down

# Testing
test: ## Run tests
	pnpm test

test-containers: docker-test ## Alias for docker-test

# Health checks
health: ## Check service health
	@echo "Checking Actions MCP Worker..."
	@curl -f http://localhost:8788/health 2>/dev/null && echo "✅ Actions MCP Worker is healthy" || echo "❌ Actions MCP Worker is down"
	@echo "Checking Remote MCP Worker..."
	@curl -f http://localhost:8789/health 2>/dev/null && echo "✅ Remote MCP Worker is healthy" || echo "❌ Remote MCP Worker is down"

docs: ## Open API documentation
	@echo "Opening API documentation..."
	@echo "Actions MCP Worker: http://localhost:8788/docs"
	@echo "Remote MCP Worker: http://localhost:8789/docs"
	@if command -v xdg-open >/dev/null; then \
		xdg-open http://localhost:8788/docs; \
		xdg-open http://localhost:8789/docs; \
	elif command -v open >/dev/null; then \
		open http://localhost:8788/docs; \
		open http://localhost:8789/docs; \
	fi

# Production deployment
deploy-build: ## Build for production deployment
	TAG=production $(MAKE) docker-build

deploy-push: ## Push images to registry
	PUSH=true DOCKER_REGISTRY=ghcr.io/username $(MAKE) docker-build

# Cleanup
clean: ## Clean build artifacts
	rm -rf packages/*/dist
	rm -rf apps/*/dist
	rm -rf node_modules
	pnpm store prune

clean-all: clean docker-clean ## Clean everything including Docker resources

# Quick start
quick-start: install build docker-build docker-up ## Full setup and start

# Aliases for convenience  
up: docker-up
down: docker-down
logs: docker-logs
restart: docker-down docker-up