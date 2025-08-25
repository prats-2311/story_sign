---
inclusion: fileMatch
fileMatchPattern: "**/ollama_service.py"
---

# AI Service Integration Guidelines

## Service Architecture

- Local vision models via Ollama for object recognition
- Cloud LLM for story generation and signing analysis
- Always implement async patterns to prevent blocking

## Error Handling Patterns

```python
try:
    response = await ai_service_call()
    if not response:
        return fallback_response()
except Exception as e:
    logger.error(f"AI service error: {e}")
    return error_response()
```

## Story Generation Requirements

- Generate 5 difficulty levels: Amateur, Normal, Mid-Level, Difficult, Expert
- Return structured JSON with titles and sentence arrays
- Implement timeout handling for long-running requests
- Add progress indicators for user feedback

## Testing Strategy

- Use mock services for unit tests
- Test with actual Ollama service for integration
- Verify JSON response structure validation
- Test timeout and error scenarios

#[[file:StorySign_Platform/backend/ollama_service.py]]
