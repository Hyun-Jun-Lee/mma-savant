# Development Environment

## System Requirements
- **Operating System**: macOS (Darwin 23.6.0)
- **Python**: 3.12+ (specified in .python-version)
- **Package Manager**: UV (modern Python package installer)
- **Container Runtime**: Docker with docker-compose

## Required Services
- **PostgreSQL 13**: Primary database
- **Redis 8.0-alpine**: Caching and session storage
- **Prefect**: Workflow orchestration for data collection

## Environment Configuration

### Environment File Setup
Copy `env.sample.txt` to `.env` and configure:
```bash
# Database
DB_HOST=localhost
DB_PORT=5432  
DB_NAME=mma_savant
DB_PASSWORD=your_password

# Redis
REDIS_PASSWORD=your_redis_password

# External APIs
LLM_API_KEY=your_openai_key
PREFECT_API_KEY=your_prefect_key
PREFECT_API_URL=your_prefect_url

# OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Development Setup Commands
```bash
# Check environment and ports
make setup

# Start all services
make up

# Enter development mode (build + start + logs)
make dev
```

## Port Configuration
Default ports used by services:
- **PostgreSQL**: 5432
- **Redis**: 6379
- **FastAPI**: (configured in docker-compose)

## Package Management
Using UV for Python package management:
```bash
# Install dependencies
uv sync

# Add new dependency
uv add package_name

# Run commands with uv
uv run pytest
uv run python script.py
```

## Docker Services
Services defined in `docker-compose.yml`:
- **savant_db**: PostgreSQL database
- **redis**: Redis cache
- **flow_serve**: Data collection service
- **savant_api**: FastAPI application (when configured)

## Development Workflow
1. Copy `env.sample.txt` to `.env` and configure
2. Run `make setup` to verify environment
3. Run `make dev` to start development environment
4. Use `make logs` to monitor service logs
5. Access individual services with make commands (db-shell, flow-shell, etc.)

## IDE Integration
- Project uses Serena MCP for enhanced IDE capabilities
- LSP support for Python development
- Type checking and code analysis