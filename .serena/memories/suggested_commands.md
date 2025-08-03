# Suggested Development Commands

## Docker Operations
```bash
# Start all services (recommended for development)
make up                   # or docker-compose up -d

# Stop all services
make down                 # or docker-compose down

# View service logs
make logs                 # or docker-compose logs -f

# Build Docker images
make build               # or docker-compose build

# Development mode (build + up + logs)
make dev
```

## Individual Service Management
```bash
# Database operations
make db-up               # Start PostgreSQL
make db-down             # Stop PostgreSQL
make db-shell            # Connect to PostgreSQL shell

# API service
make api-up              # Start API service
make api-down            # Stop API service
make api-restart         # Restart API service

# Flow service (data collection)
make flow-up             # Start data collection service
make flow-down           # Stop data collection service
make flow-shell          # Access flow_serve container shell
```

## Data Collection
```bash
# Run data scraping workflow
make run-scraper         # Run main scraping workflow

# Manual scraper execution (inside src/data_collector)
python main.py           # Run main workflow
python scrapers/fighters_scraper.py    # Individual scraper
```

## Testing
```bash
# Run all tests
uv run pytest           # Using uv package manager

# Run specific test modules
uv run pytest src/tests/fighter/ -v
uv run pytest src/data_collector/workflows/tests/ -v

# Run scraper tests
make test-scraper        # Run workflow tests
```

## Database Management
```bash
# Initialize database tables
cd src && python database/init_tables.py

# Initialize weight classes (after table creation)
cd src && python -c "from data_collector.workflows.tasks import init_weight_classes; init_weight_classes()"
```

## Environment Setup
```bash
# Check environment configuration
make check-env

# Check port availability  
make check-ports

# Complete setup
make setup               # check-env + check-ports

# Clean Docker resources
make clean
```

## System Commands (macOS/Darwin)
- `ls` - List files
- `cd` - Change directory
- `grep` - Search text (prefer `rg` ripgrep)
- `find` - Find files
- `git` - Version control operations