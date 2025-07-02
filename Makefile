# MMA Savant Makefile
# Simplifies deployment and operation tasks

.PHONY: help check-env check-ports setup build up down logs clean test init-db run-scraper dev status restart flow-shell flow-up flow-down flow-restart db-up db-down db-restart api-up api-down api-restart

# Default target
help:
	@echo "MMA Savant - Available Commands:"
	@echo ""
	@echo "🛠️  Setup & Environment:"
	@echo "  make setup       - Complete setup (env + ports + build)"
	@echo "  make check-env   - Check .env file and required variables"
	@echo "  make check-ports - Check if required ports are available"
	@echo ""
	@echo "🐳 Docker Operations:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services (detached)"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - Show service logs"
	@echo "  make status      - Show container status"
	@echo ""
	@echo "🚢 Individual Service Operations:"
	@echo "  make flow-shell  - Access flow_serve container shell"
	@echo "  make flow-up     - Start flow_serve service"
	@echo "  make flow-down   - Stop flow_serve service"
	@echo "  make flow-restart - Restart flow_serve service"
	@echo "  make db-up       - Start database service"
	@echo "  make db-down     - Stop database service"
	@echo "  make db-restart  - Restart database service"
	@echo "  make api-up      - Start API service"
	@echo "  make api-down    - Stop API service"
	@echo "  make api-restart - Restart API service"
	@echo ""
	@echo "🗄️  Database Operations:"
	@echo "  make db-shell    - Connect to PostgreSQL shell"
	@echo ""
	@echo "🕷️  Data Collection:"
	@echo "  make run-scraper - Run data collection workflow"
	@echo "  make test-scraper        - Run tests"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean       - Clean Docker resources"
	@echo "  make dev         - Development mode (build + up + logs)"

# Environment and port checking
check-env:
	@echo "🔍 Checking environment configuration..."
	@chmod +x build_script/check_env.sh
	@./build_script/check_env.sh

check-ports:
	@echo "🔍 Checking port availability..."
	@chmod +x build_script/check_ports.sh
	@./build_script/check_ports.sh

# Complete setup process
setup: check-env check-ports
	@echo "✅ Environment setup complete!"

# Docker operations
build:
	@echo "🔨 Building Docker images..."
	docker-compose build

up: check-env
	@echo "🚀 Starting services..."
	docker-compose up -d

down:
	@echo "🛑 Stopping services..."
	docker-compose down

restart: down up
	@echo "♻️  Services restarted!"

logs:
	@echo "📋 Showing service logs..."
	docker-compose logs -f

status:
	@echo "📊 Container status:"
	docker-compose ps

# Database operations
db-shell:
	@echo "🐘 Connecting to PostgreSQL..."
	docker-compose exec savant_db psql -U postgres -d $$(grep DB_NAME .env | cut -d'=' -f2)

# Data collection operations
run-scraper: up
	@echo "🕷️  Running data collection workflow..."
	docker-compose exec flow_serve python main.py

test-scraper:
	@echo "🧪 Running tests..."
	python -m pytest src/data_collector/workflows/tests/test_ufc_stats_flow.py -v

# Development mode
dev: build up
	@echo "🚧 Development mode - showing logs..."
	@make logs

# Maintenance
clean:
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup complete!"

# Individual service operations
flow-shell:
	@echo "🐚 Accessing flow_serve shell..."
	docker-compose exec flow_serve /bin/bash

# Individual service up commands
flow-up:
	@echo "🚀 Starting flow_serve service..."
	docker-compose up -d flow_serve

db-up:
	@echo "🚀 Starting database service..."
	docker-compose up -d savant_db

api-up:
	@echo "🚀 Starting API service..."
	docker-compose up -d savant_api

# Individual service down commands
flow-down:
	@echo "🛑 Stopping flow_serve service..."
	docker-compose stop flow_serve

db-down:
	@echo "🛑 Stopping database service..."
	docker-compose stop savant_db

api-down:
	@echo "🛑 Stopping API service..."
	docker-compose stop savant_api

# Individual service restart commands
flow-restart: flow-down flow-up
	@echo "♻️  flow_serve service restarted!"

db-restart: db-down db-up
	@echo "♻️  Database service restarted!"

api-restart: api-down api-up
	@echo "♻️  API service restarted!"

# Quick status check
quick-check: check-env check-ports status
	@echo "📈 System status check complete!"