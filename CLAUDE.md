# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MMA Savant is a comprehensive Mixed Martial Arts data collection and analysis platform consisting of:
- **Data Collector**: Automated web scrapers using Playwright and httpx for collecting UFC stats
- **Backend API**: FastAPI service providing REST endpoints for fighter, event, and match data
- **Chat Interface**: Chainlit-powered conversational interface for querying MMA data
- **Database**: PostgreSQL with comprehensive MMA schema and Redis for caching

## Architecture

### Core Data Flow
1. **Scrapers** (`src/data_collector/scrapers/`) collect data from UFC stats using Playwright
2. **Workflows** (`src/data_collector/workflows/`) orchestrate scraping tasks using Prefect
3. **Repository Pattern** manages data persistence with SQLAlchemy models
4. **API Services** expose data through FastAPI endpoints with domain-specific modules

### Key Components
- **Models**: SQLAlchemy models with corresponding Pydantic schemas for validation
- **Repositories**: Data access layer implementing repository pattern
- **Services**: Business logic layer between API and repositories
- **Database Session Management**: Context managers for transaction handling

## Development Commands

### Running the Application
```bash
# Start all services (PostgreSQL, Redis, data collector)
docker-compose up -d

# Run data collection workflow manually
cd src/data_collector
python main.py

# Run specific test workflow
python -m pytest src/data_collector/workflows/tests/test_ufc_stats_flow.py

# Run individual scraper tests
python src/data_collector/scrapers/test-by-html/test_fighters.py
```

### Database Operations
```bash
# Initialize database tables
cd src
python database/init_tables.py

# Initialize weight classes (run after table creation)
python -c "from data_collector.workflows.tasks import init_weight_classes; init_weight_classes()"
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest src/data_collector/workflows/tests/test_ufc_stats_flow.py -v

# Run scraper validation tests
python src/data_collector/scrapers/test-by-html/test_event_detail.py
```

## Configuration

### Environment Variables
Create `.env` file with:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=ufc_stats
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
LLM_API_KEY=your_openai_key
PREFECT_API_KEY=your_prefect_key
PREFECT_API_URL=your_prefect_url
```

### Database Configuration
- Uses `src/config.py` for centralized configuration management
- PostgreSQL connection via asyncpg for async operations
- Redis for caching with configurable authentication

## Data Models Architecture

### Core Entities
- **Fighter**: Profile, stats, physical attributes with win/loss records
- **Event**: UFC events with date, location, and associated matches
- **Match**: Individual fights with detailed statistics and outcomes
- **Ranking**: Fighter rankings by weight class with historical tracking
- **WeightClass**: UFC weight divisions with boundaries

### Key Relationships
- Fighters have many-to-many relationships with matches via `fighter_match` table
- Rankings link fighters to weight classes with temporal data
- Events contain multiple matches with detailed statistics

## Workflow Management

### Prefect Integration
- `src/data_collector/workflows/ufc_stats_flow.py`: Main scraping orchestration
- Scheduled execution via `src/data_collector/main.py` (weekly on Wednesdays)
- Task-based architecture for modular scraping operations

### Scraping Strategy
- **Playwright**: For JavaScript-heavy pages requiring browser automation
- **httpx**: For static content and API endpoints
- **Session Management**: Database sessions with proper cleanup
- **Error Handling**: Comprehensive logging and retry mechanisms

## API Structure

### Domain Organization
Each domain (`fighter/`, `event/`, `match/`) follows consistent structure:
- `models.py`: SQLAlchemy models and Pydantic schemas
- `repositories.py`: Data access layer
- `services.py`: Business logic
- `dto.py`: Data transfer objects (where applicable)

### Database Sessions
Use context managers for proper session handling:
```python
from database.session import db_session

with db_session() as session:
    # Database operations
    pass
```

## Testing Strategy

### Test Organization
- Unit tests in `src/data_collector/workflows/tests/`
- Scraper validation tests in `src/data_collector/scrapers/test-by-html/`
- Manual testing scripts in `src/test.py`

### Running Scrapers
Individual scrapers can be tested with saved HTML files in `test-by-html/` directory for development without hitting live endpoints.