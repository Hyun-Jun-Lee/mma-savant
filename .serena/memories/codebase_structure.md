# Codebase Structure

## Root Level
```
mma-savant/
├── src/                    # Main backend application
├── crawlers/              # Data collection crawlers (separate from src)
├── frontend/              # Frontend application  
├── init_sqls/             # Database initialization scripts
├── build_script/          # Build and setup scripts
├── docs/                  # Project documentation
├── docker-compose.yml     # Docker services configuration
├── Dockerfile_serve       # Docker image for data collection
├── Makefile              # Development commands
└── README.md             # Project overview in Korean
```

## Source Code Structure (src/)
```
src/
├── api/                   # API layer
│   ├── auth/             # Authentication & JWT handling
│   ├── chat/             # Chat session management
│   ├── user/             # User management APIs  
│   └── websocket/        # WebSocket connections
├── common/               # Shared utilities and base models
├── composition/          # Complex data composition services
├── conversation/         # Chat conversation management
├── database/             # Database connections and sessions
├── data_collector/       # Web scraping and data collection
│   ├── scrapers/         # Individual scraper modules
│   └── workflows/        # Prefect workflow orchestration
├── event/                # Event domain (UFC events)
├── exceptions/           # Exception definitions
├── fighter/              # Fighter domain (fighters, rankings)
├── llm/                  # LLM integration (OpenAI, Anthropic)
├── match/                # Match domain (fights, statistics)
├── tests/                # Test suite organized by domain
├── tools/                # MCP tools for data querying
├── user/                 # User domain (authentication, profiles)
├── config.py             # Configuration management
├── main_api.py           # FastAPI application entry point
└── pyproject.toml        # Python project configuration
```

## Domain Architecture
Each domain (fighter, event, match, user) follows consistent structure:
- `models.py` - SQLAlchemy models and Pydantic schemas
- `repositories.py` - Data access layer
- `services.py` - Business logic layer  
- `exceptions.py` - Domain-specific exceptions
- `dto.py` - Data Transfer Objects (optional)
- `routers.py` - API routes (if applicable)

## Key Configuration Files
- **pyproject.toml**: Python dependencies and project metadata
- **docker-compose.yml**: PostgreSQL, Redis, and application services
- **Makefile**: Development workflow commands
- **docs/CLAUDE.md**: Detailed development guidelines
- **.env**: Environment variables (copy from env.sample.txt)

## Testing Structure
- Tests mirror source structure in `src/tests/`
- Domain-specific test directories (fighter/, match/, event/)
- Shared fixtures in `conftest.py`
- Database testing with separate test database