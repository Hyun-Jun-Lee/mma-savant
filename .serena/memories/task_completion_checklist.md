# Task Completion Checklist

When completing development tasks in MMA Savant, follow this checklist:

## Code Quality
- [ ] Follow domain structure conventions (models, repositories, services)
- [ ] Use proper async/await patterns for database operations
- [ ] Implement proper error handling with domain-specific exceptions
- [ ] Add type hints where appropriate
- [ ] Use repository pattern for data access

## Testing
- [ ] Run relevant tests to ensure no regressions:
```bash
# Run all tests
uv run pytest

# Run domain-specific tests
uv run pytest src/tests/fighter/ -v
uv run pytest src/tests/match/ -v
uv run pytest src/tests/event/ -v
```

## Database Operations
- [ ] Use proper session management with context managers
- [ ] Test database operations don't break existing functionality
- [ ] Verify migrations if schema changes were made

## API Changes
- [ ] Test API endpoints if modified
- [ ] Ensure proper error responses
- [ ] Check authentication/authorization if applicable

## Data Collection (if applicable)
- [ ] Test scrapers if modified:
```bash
# Test scraping workflow
make test-scraper

# Test individual scrapers
python src/data_collector/scrapers/test-by-html/test_*.py
```

## Environment & Dependencies
- [ ] Update pyproject.toml if new dependencies added
- [ ] Check environment configuration still works
- [ ] Verify Docker services start properly:
```bash
make setup    # Check environment
make dev      # Test full stack
```

## Documentation
- [ ] Update CLAUDE.md if significant architectural changes
- [ ] Add comments for complex business logic
- [ ] Update API documentation if endpoints changed

## Final Verification
- [ ] All services start without errors
- [ ] Database connections work
- [ ] Redis caching functional (if applicable)
- [ ] No breaking changes to existing functionality

## Deployment Readiness
- [ ] Docker images build successfully
- [ ] Environment variables properly configured
- [ ] Database migrations ready (if applicable)
- [ ] All tests passing