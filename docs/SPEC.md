# MMA Savant Development Specification

## Core Architecture Principles

### 1. Domain-Driven Design (DDD)
- **Domain Separation**: Each domain (fighter, event, match, user, etc.) is a self-contained module
- **Clear Boundaries**: Domains communicate through well-defined interfaces
- **Single Responsibility**: Each domain handles only its specific business logic

### 2. Layered Architecture
```
Composition Layer (High-level business operations)
    ↓
Service Layer (Business logic coordination)
    ↓
Repository Layer (Data access abstraction)
    ↓
Model Layer (Data models and schemas)
    ↓
Database Layer (SQLAlchemy + PostgreSQL)
```

### 3. Async-First Design
- **Async/Await**: All I/O operations use async patterns
- **Session Management**: Async database sessions with proper context management
- **Workflow Orchestration**: Prefect for complex async workflows

## Project Structure Conventions

### Domain Module Structure
```
domain/
├── __init__.py
├── models.py          # SQLAlchemy models + Pydantic schemas
├── repositories.py    # Data access functions
├── services.py        # Business logic coordination
├── dto.py             # Data Transfer Objects for service layer
├── exceptions.py      # Domain-specific exceptions
└── test/
    └── test_*.py
```

### File Organization Rules
- **models.py**: Contains both SQLAlchemy models and Pydantic schemas
- **repositories.py**: Pure data access functions, no business logic
- **services.py**: Coordinates business operations, calls repositories
- **dto.py**: Complex data combinations and transformations
- **exceptions.py**: Custom exception classes for the domain

## Data Model Patterns

### Model/Schema Separation
```python
# SQLAlchemy Model
class FighterModel(BaseModel):
    __tablename__ = "fighter"
    name = Column(String, nullable=False)
    # ... other fields
    
    @classmethod
    def from_schema(cls, schema: FighterSchema) -> 'FighterModel':
        return cls(name=schema.name, ...)
        
    def to_schema(self) -> FighterSchema:
        return FighterSchema(id=self.id, name=self.name, ...)

# Pydantic Schema
class FighterSchema(BaseSchema):
    name: str
    nickname: Optional[str] = None
    # ... other fields
    
    model_config = ConfigDict(from_attributes=True)
```

### Base Model Requirements
- **BaseModel**: All SQLAlchemy models inherit from `BaseModel`
- **BaseSchema**: All Pydantic schemas inherit from `BaseSchema`
- **Standardized Fields**: `id`, `created_at`, `updated_at` are automatically included
- **Bidirectional Conversion**: Models must provide `from_schema()` and `to_schema()` methods

## Repository Pattern

### Repository Function Signatures
```python
# Query functions - return schemas
async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> Optional[FighterSchema]:
    # Always return Pydantic schemas, never SQLAlchemy models
    
async def get_all_fighters(session: AsyncSession) -> List[FighterSchema]:
    # Use list comprehension with to_schema()
    
# Mutation functions - accept schemas
async def create_fighter(session: AsyncSession, fighter: FighterSchema) -> FighterSchema:
    # Create from schema, return updated schema
    
async def update_fighter(session: AsyncSession, fighter_id: int, updates: Dict[str, Any]) -> Optional[FighterSchema]:
    # Update and return schema
```

### Repository Rules
- **Session Injection**: Always accept `AsyncSession` as first parameter
- **Schema Returns**: Always return Pydantic schemas, never SQLAlchemy models
- **Pure Functions**: No business logic, only data access
- **Error Handling**: Let exceptions propagate to service layer

## Service Layer Pattern

### Service Function Structure
```python
async def get_fighter_by_name(session: AsyncSession, name: str) -> Optional[FighterWithRankingsDTO]:
    # 1. Call repository for base data
    fighter = await fighter_repo.get_fighter_by_name(session, name)
    
    # 2. Handle not found with domain exception
    if not fighter:
        raise fighter_exc.FighterNotFoundError(name)
    
    # 3. Orchestrate additional data collection
    return await _build_fighter_with_rankings(session, fighter)
```

### Service Layer Rules
- **Coordination**: Orchestrate multiple repository calls
- **Exception Handling**: Convert repository errors to domain exceptions
- **Business Logic**: Apply domain rules and validations
- **DTO Construction**: Build complex DTOs from multiple data sources

## DTO Pattern

### DTO Design Guidelines
```python
class FighterWithRankingsDTO(BaseModel):
    """Fighter 기본 정보 + 랭킹 정보 (가장 기본적인 조합)"""
    fighter: FighterSchema
    rankings: Dict[str, int] = Field(
        example={"Lightweight": 5, "Welterweight": 12}
    )

class WeightClassRankingsDTO(BaseModel):
    """특정 체급의 랭킹 리스트"""
    weight_class_name: str
    rankings: List[RankedFighterDTO]
```

### DTO Rules
- **Composition**: Combine multiple schemas into meaningful business objects
- **Documentation**: Include clear docstrings and field examples
- **Validation**: Use Pydantic validation for business rules
- **Naming**: Suffix with `DTO` for clarity

## Composition Layer Pattern

### High-Level Business Operations
```python
async def get_fighter_all_matches(session: AsyncSession, fighter_id: int) -> List[Dict]:
    """
    특정 선수의 모든 경기 기록을 조회합니다.
    """
    # 1. Get base data from repositories
    fighter_matches = await get_fighters_matches(session, fighter_id, limit=None)
    
    # 2. Orchestrate complex data collection
    results = []
    for fm in fighter_matches:
        match = await get_match_by_id(session, fm.match_id)
        event = await get_event_by_id(session, match.event_id)
        # ... more data collection
        
        results.append({
            "event": event,
            "match": match,
            "result": fm.result,
            # ... composed result
        })
    
    return results
```

### Composition Rules
- **Cross-Domain Operations**: Coordinate between multiple domains
- **Complex Aggregations**: Handle multi-step data collection
- **Business Context**: Provide meaningful business operations
- **Performance**: Optimize for minimal database queries

## Database Session Management

### Session Pattern
```python
# In workflows and main operations
async with async_db_session() as session:
    result = await some_service_function(session, params)
    
# Session is automatically committed/rolled back
```

### Session Rules
- **Context Manager**: Always use `async_db_session()` context manager
- **Automatic Commit**: Session commits automatically on success
- **Automatic Rollback**: Session rolls back on exceptions
- **One Session Per Operation**: Don't share sessions across operations

## Exception Handling

### Custom Exception Pattern
```python
# Domain-specific exceptions
class FighterNotFoundError(Exception):
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Fighter not found: {identifier}")

class InvalidWeightClassError(Exception):
    def __init__(self, weight_class: str):
        self.weight_class = weight_class
        super().__init__(f"Invalid weight class: {weight_class}")
```

### Exception Rules
- **Domain-Specific**: Each domain defines its own exceptions
- **Meaningful Messages**: Include relevant context in error messages
- **Service Layer**: Convert repository errors to domain exceptions
- **Propagation**: Let exceptions bubble up to appropriate handlers

## Workflow Pattern

### Prefect Flow Structure
```python
@flow(log_prints=True)
async def run_ufc_stats_flow():
    logger.info("Start UFC stats scraping")
    
    # Separate session for each major operation
    async with async_db_session() as session:
        await scrap_all_events_task(session, crawl_with_httpx)
    
    async with async_db_session() as session:
        await scrap_all_fighter_task(session, crawl_with_httpx)
    
    logger.info("UFC stats scraping completed")
```

### Workflow Rules
- **Task Isolation**: Each major task gets its own session
- **Logging**: Comprehensive logging for monitoring
- **Error Handling**: Let Prefect handle task failures
- **Dependency Injection**: Pass dependencies (crawlers, sessions) as parameters

## Type Safety Requirements

### Type Hints
```python
from typing import List, Optional, Dict, Any, Literal
from sqlalchemy.ext.asyncio import AsyncSession

# All function signatures must include complete type hints
async def get_top_fighters_by_record(
    session: AsyncSession, 
    record: Literal["win", "loss", "draw"], 
    weight_class_id: Optional[int] = None, 
    limit: int = 10
) -> List[RankedFighterDTO]:
    pass
```

### Type Safety Rules
- **Complete Annotations**: All parameters and return types must be annotated
- **Import Types**: Import all necessary types from `typing`
- **Optional Handling**: Use `Optional[T]` for nullable values
- **Generic Types**: Use `List[T]`, `Dict[K, V]` for collections

## Naming Conventions

### Function Naming
- **Repository Functions**: `get_*`, `create_*`, `update_*`, `delete_*`
- **Service Functions**: Business-meaningful names (e.g., `get_fighter_by_name`)
- **Composition Functions**: High-level operation names (e.g., `get_fighter_all_matches`)
- **Private Helpers**: Prefix with `_` (e.g., `_build_fighter_with_rankings`)

### Class Naming
- **Models**: `*Model` suffix (e.g., `FighterModel`)
- **Schemas**: `*Schema` suffix (e.g., `FighterSchema`)
- **DTOs**: `*DTO` suffix (e.g., `FighterWithRankingsDTO`)
- **Exceptions**: `*Error` suffix (e.g., `FighterNotFoundError`)

## Testing Guidelines

### Repository Testing
```python
@pytest.mark.asyncio
async def test_get_fighter_by_id():
    async with async_db_session() as session:
        # Test with real database operations
        fighter = await get_fighter_by_id(session, 1)
        assert fighter is not None
        assert isinstance(fighter, FighterSchema)
```

### Service Testing
```python
@pytest.mark.asyncio
async def test_get_fighter_by_name_not_found():
    async with async_db_session() as session:
        with pytest.raises(FighterNotFoundError):
            await get_fighter_by_name(session, "NonExistentFighter")
```

### Testing Rules
- **Async Tests**: Use `@pytest.mark.asyncio` for async tests
- **Real Sessions**: Use actual database sessions for integration tests
- **Exception Testing**: Test both success and failure scenarios
- **Schema Validation**: Assert return types are correct schemas

## Configuration Management

### Environment Configuration
```python
from config import get_database_url

DATABASE_URL = get_database_url()
```

### Configuration Rules
- **Centralized Config**: All configuration in `config.py`
- **Environment Variables**: Use environment variables for deployment config
- **Default Values**: Provide sensible defaults for development
- **Type Safety**: Validate configuration types

## Code Quality Standards

### Documentation
- **Type Hints**: Complete type annotations for all public functions
- **Docstrings**: Korean language docstrings for business logic
- **Comments**: Minimal comments, let code be self-documenting
- **Examples**: Include examples in DTO field definitions

### Performance
- **Async Operations**: Use async/await for all I/O operations
- **Query Optimization**: Use joins to minimize database queries
- **Session Management**: Proper session lifecycle management
- **Batch Operations**: Use batch operations where possible

### Security
- **Input Validation**: Validate all external inputs through Pydantic
- **SQL Injection**: Use parameterized queries through SQLAlchemy
- **Error Handling**: Don't expose internal errors to users
- **Logging**: Log errors but not sensitive information

## Extension Guidelines

### Adding New Domains
1. Create domain directory with standard structure
2. Define models with both SQLAlchemy and Pydantic schemas
3. Implement repository functions following the pattern
4. Add service layer for business logic
5. Create DTOs for complex operations
6. Add composition functions if needed

### Modifying Existing Domains
1. Update models first (schema + model)
2. Update repository functions
3. Update service functions
4. Update DTOs as needed
5. Update composition functions
6. Update tests

### Cross-Domain Operations
- Use composition layer for operations spanning multiple domains
- Inject sessions rather than creating new ones
- Handle domain exceptions appropriately
- Maintain clear separation of concerns

---

**IMPORTANT**: This specification must be followed consistently across all modules. Any deviations should be discussed and documented. When extending the codebase, LLM assistants should strictly adhere to these patterns to maintain architectural consistency.