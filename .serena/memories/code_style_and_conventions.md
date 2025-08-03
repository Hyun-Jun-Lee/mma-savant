# Code Style and Conventions

## Python Version & Package Management
- **Python Version**: 3.12+ (specified in pyproject.toml)
- **Package Manager**: UV (recommended, faster than pip)
- **Dependency Management**: pyproject.toml with uv.lock

## Code Organization

### Domain Structure
Each domain follows consistent organization:
```
domain_name/
├── models.py       # SQLAlchemy models + Pydantic schemas  
├── repositories.py # Data access layer
├── services.py     # Business logic layer
├── dto.py         # Data Transfer Objects (optional)
├── exceptions.py  # Domain-specific exceptions
└── routers.py     # API routes (if applicable)
```

### Database Patterns
- **Repository Pattern**: Data access abstraction
- **Session Management**: Use context managers
```python
from database.session import async_db_session

async with async_db_session() as session:
    # database operations
```

### Model Conventions
- **SQLAlchemy Models**: Inherit from `BaseModel` 
- **Pydantic Schemas**: Separate schemas for validation
- **Naming**: PascalCase for classes, snake_case for functions/variables

### Error Handling
- **Domain Exceptions**: Custom exception classes per domain
- **Base Exceptions**: Inherit from domain-specific base classes
- **Error Responses**: Structured error responses in APIs

## Testing Conventions

### Test Organization
- **Test Structure**: Mirror source structure in `src/tests/`
- **Test Framework**: pytest with async support
- **Test Database**: Separate test database with fixtures
- **Mocking**: Use pytest fixtures for database operations

### Test Naming
- Test classes: `TestClassName`
- Test methods: `test_function_name`
- Test files: `test_module_name.py`

## Import Organization
- Standard library imports first
- Third-party imports second  
- Local imports last
- Use absolute imports for clarity

## Configuration Management
- **Environment Variables**: Centralized in `src/config.py`
- **Settings**: Pydantic Settings for validation
- **Database URLs**: Constructed from environment variables

## Async/Await Patterns
- Use async/await for database operations
- SQLAlchemy with asyncpg for PostgreSQL
- Proper session management in async context