# Frontend Tests

## Directory Structure

- `unit/` - Unit tests for individual components, hooks, services, etc.
- `integration/` - Integration tests for component interactions
- `e2e/` - End-to-end tests for complete user workflows
- `accessibility/` - Accessibility compliance tests
- `performance/` - Performance and optimization tests

## Running Tests

```bash
# Run all tests
npm test

# Run specific test category
npm test -- --testPathPattern=unit
npm test -- --testPathPattern=integration
npm test -- --testPathPattern=e2e

# Run with coverage
npm test -- --coverage
```
