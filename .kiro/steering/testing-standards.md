---
inclusion: fileMatch
fileMatchPattern: "**/test_*.py"
---

# Testing Standards for StorySign

## Test Structure Requirements

- Use pytest for all backend tests
- Mock external services (Ollama, MediaPipe) for unit tests
- Integration tests should test actual service connections
- Performance tests must verify <100ms latency requirements

## Test Categories

1. **Unit Tests**: Individual function testing with mocks
2. **Integration Tests**: WebSocket communication, API endpoints
3. **Performance Tests**: Latency benchmarks, memory usage
4. **End-to-End Tests**: Complete user workflows

## Mock Patterns

```python
@pytest.fixture
def mock_ollama_service():
    with patch('backend.ollama_service.OllamaService') as mock:
        mock.return_value.generate_story.return_value = {
            "amateur": {"title": "Test Story", "sentences": ["Test sentence"]}
        }
        yield mock
```

## Performance Test Requirements

- Video processing latency < 100ms
- WebSocket message handling < 50ms
- AI service response timeout at 30s
- Memory usage monitoring for long sessions

#[[file:StorySign_Platform/backend/test_*.py]]
