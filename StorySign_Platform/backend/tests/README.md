# Backend Tests

## Directory Structure

- `unit/` - Unit tests for individual functions and classes
- `integration/` - Integration tests for API endpoints and services
- `e2e/` - End-to-end tests for complete backend workflows

## Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=backend
```
