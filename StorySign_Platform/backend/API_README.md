# StorySign ASL Platform - Comprehensive REST API

This document describes the comprehensive REST API implementation for the StorySign ASL Platform, including authentication, user management, content management, GraphQL support, rate limiting, and comprehensive testing tools.

## 🚀 Features

### Core API Features

- **JWT Authentication** - Secure user authentication with access and refresh tokens
- **Rate Limiting** - Intelligent rate limiting with burst allowance and IP blocking
- **GraphQL Support** - Complex queries with a single endpoint
- **Comprehensive Documentation** - Auto-generated OpenAPI/Swagger docs with examples
- **Testing Suite** - Comprehensive API testing with detailed reporting

### API Endpoints

- **Authentication** (`/api/v1/auth/`) - User registration, login, token management
- **User Management** (`/api/v1/users/`) - Profile management, preferences, analytics
- **Content Management** (`/api/v1/content/`) - Story creation, search, rating
- **ASL World** (`/api/asl-world/`) - Story generation and ASL-specific features
- **GraphQL** (`/api/v1/graphql`) - Complex queries and mutations
- **Documentation** (`/api/v1/docs/`) - API documentation and testing tools

### Security & Performance

- **Middleware Stack** - Authentication, rate limiting, CORS, request tracking
- **Role-based Access Control** - Different permissions for learners, educators, admins
- **API Key Support** - For external integrations and webhooks
- **Comprehensive Error Handling** - Consistent error responses with detailed information

## 📋 Prerequisites

- Python 3.8+
- FastAPI and dependencies (see requirements_api.txt)
- Database (PostgreSQL/MySQL/TiDB)
- Redis (optional, for caching and session management)

## 🛠️ Installation

### 1. Install Dependencies

```bash
# Install API dependencies
python install_api_deps.py

# Or manually install
pip install -r requirements_api.txt
```

### 2. Configure Environment

Create a `.env` file or configure environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/storysign
# or for TiDB
DATABASE_URL=mysql://user:password@localhost:4000/storysign

# JWT Secret (change in production!)
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Redis (optional)
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
```

### 3. Database Setup

```bash
# Run database migrations
python -m alembic upgrade head

# Or create tables manually
python -c "from core.database_service import DatabaseService; DatabaseService().create_tables()"
```

## 🚀 Running the API

### Development Server

```bash
# Start the API server
python main_api.py

# With custom configuration
python main_api.py --host 0.0.0.0 --port 8000 --reload

# Production server with Gunicorn
gunicorn main_api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_api.txt .
RUN pip install -r requirements_api.txt

COPY . .
EXPOSE 8000

CMD ["python", "main_api.py", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 API Documentation

### Interactive Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/api/v1/openapi.json
- **Custom Docs**: http://localhost:8000/api/v1/docs/

### Authentication

Most endpoints require authentication. Get a token by registering or logging in:

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "password": "SecurePass123!"
  }'
```

Use the returned `access_token` in subsequent requests:

```bash
curl -X GET "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Rate Limiting

The API implements intelligent rate limiting:

- **Default**: 100 requests/hour with burst of 20
- **Authentication**: 5 login attempts per 5 minutes
- **Story Generation**: 20 requests/hour
- **Role-based**: Higher limits for educators and admins

Rate limit information is included in response headers:

- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: When the window resets

## 🧪 Testing

### Comprehensive Test Suite

Run the complete API test suite:

```bash
# Run all tests
python run_api_tests.py

# Test specific URL
python run_api_tests.py --url http://api.example.com

# Generate detailed reports
python run_api_tests.py --output results.json --html-report report.html

# Quiet mode (CI/CD friendly)
python run_api_tests.py --quiet
```

### Manual Testing

Test individual endpoints:

```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/api/v1/docs/endpoints

# Test with authentication
curl -X GET "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### GraphQL Testing

Test GraphQL queries:

```bash
curl -X POST "http://localhost:8000/api/v1/graphql" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { me { id username fullName } }"
  }'
```

## 📊 API Endpoints Reference

### Authentication (`/api/v1/auth/`)

| Endpoint           | Method | Description            | Auth Required |
| ------------------ | ------ | ---------------------- | ------------- |
| `/register`        | POST   | Register new user      | No            |
| `/login`           | POST   | User login             | No            |
| `/refresh`         | POST   | Refresh access token   | No            |
| `/logout`          | POST   | Logout current session | Yes           |
| `/logout-all`      | POST   | Logout all sessions    | Yes           |
| `/change-password` | POST   | Change password        | Yes           |
| `/me`              | GET    | Get current user info  | Yes           |
| `/sessions`        | GET    | List user sessions     | Yes           |

### User Management (`/api/v1/users/`)

| Endpoint              | Method  | Description            | Auth Required |
| --------------------- | ------- | ---------------------- | ------------- |
| `/profile`            | GET     | Get user profile       | Yes           |
| `/profile`            | PUT     | Update user profile    | Yes           |
| `/{user_id}`          | GET     | Get user by ID         | Yes           |
| `/search`             | POST    | Search users           | Yes           |
| `/progress/summary`   | GET     | Get progress summary   | Yes           |
| `/analytics/detailed` | GET     | Get detailed analytics | Yes           |
| `/preferences`        | GET/PUT | Manage preferences     | Yes           |
| `/learning-goals`     | GET/PUT | Manage learning goals  | Yes           |

### Content Management (`/api/v1/content/`)

| Endpoint               | Method | Description          | Auth Required |
| ---------------------- | ------ | -------------------- | ------------- |
| `/stories`             | GET    | List stories         | Yes           |
| `/stories`             | POST   | Create story         | Yes           |
| `/stories/{id}`        | GET    | Get story details    | Yes           |
| `/stories/{id}`        | PUT    | Update story         | Yes           |
| `/stories/search`      | POST   | Search stories       | Yes           |
| `/stories/popular`     | GET    | Get popular stories  | Yes           |
| `/stories/featured`    | GET    | Get featured stories | Yes           |
| `/stories/{id}/rating` | POST   | Rate story           | Yes           |

### GraphQL (`/api/v1/graphql`)

Single endpoint supporting queries and mutations:

**Example Queries:**

```graphql
# Get current user
query {
  me {
    id
    username
    fullName
  }
}

# Search users
query {
  users(search: { limit: 10 }) {
    id
    username
  }
}

# Get user progress
query {
  myProgress {
    skillArea
    currentLevel
  }
}

# Get stories
query {
  stories(search: { limit: 5 }) {
    id
    title
    difficultyLevel
  }
}
```

**Example Mutations:**

```graphql
# Update learning goals
mutation {
  updateLearningGoals(goals: ["improve-fingerspelling"])
}

# Update preferences
mutation {
  updatePreferences(preferences: "{\"theme\":\"dark\"}")
}
```

## 🔧 Configuration

### Rate Limiting Configuration

Customize rate limits in `main_api.py`:

```python
rate_limiting_middleware = RateLimitingMiddleware(
    app,
    default_rate_limit=RateLimit(requests=100, window=3600, burst=20),
    endpoint_limits={
        "/api/v1/auth/login": RateLimit(5, 300, 2),
        "/api/v1/auth/register": RateLimit(3, 3600, 1),
        # Add more endpoint-specific limits
    },
    user_limits={
        "admin": RateLimit(1000, 3600, 100),
        "educator": RateLimit(500, 3600, 50),
        "learner": RateLimit(200, 3600, 30),
    }
)
```

### Authentication Configuration

Configure JWT settings:

```python
auth_config = {
    "jwt_secret": "your-secret-key",
    "jwt_algorithm": "HS256",
    "access_token_expire_minutes": 15,
    "refresh_token_expire_days": 7
}
```

### Database Configuration

Configure database connection in `config.py`:

```python
DATABASE_CONFIG = {
    "url": "postgresql://user:password@localhost/storysign",
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30
}
```

## 🚨 Error Handling

The API returns consistent error responses:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "timestamp": 1234567890.123,
  "status_code": 400,
  "path": "/api/v1/endpoint"
}
```

Common error types:

- `validation_error` - Request validation failed
- `authentication_failed` - Invalid or missing authentication
- `rate_limit_exceeded` - Rate limit exceeded
- `resource_not_found` - Requested resource not found
- `internal_server_error` - Server error

## 📈 Monitoring & Metrics

### Health Checks

- **Basic Health**: `GET /health`
- **Detailed Health**: `GET /api/v1/docs/health`
- **Metrics**: `GET /metrics`

### Logging

The API logs to both console and file (`storysign_api.log`):

```python
# Configure logging level
logging.basicConfig(level=logging.INFO)

# Custom logger
logger = logging.getLogger("storysign.api")
```

### Performance Monitoring

Response headers include performance information:

- `X-Process-Time`: Request processing time
- `X-Request-ID`: Unique request identifier
- `X-RateLimit-*`: Rate limiting information

## 🔒 Security Considerations

### Production Deployment

1. **Change JWT Secret**: Use a strong, unique JWT secret
2. **HTTPS Only**: Always use HTTPS in production
3. **Database Security**: Use connection pooling and prepared statements
4. **Rate Limiting**: Configure appropriate rate limits
5. **CORS**: Configure CORS for your domain only
6. **Input Validation**: All inputs are validated with Pydantic
7. **SQL Injection**: Protected by SQLAlchemy ORM
8. **XSS Protection**: JSON responses prevent XSS

### Environment Variables

```bash
# Production environment variables
JWT_SECRET=your-super-secret-production-key
DATABASE_URL=postgresql://user:password@db-host/storysign
REDIS_URL=redis://redis-host:6379
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
LOG_LEVEL=warning
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Install dependencies: `python install_api_deps.py`
3. Run tests: `python run_api_tests.py`
4. Make changes and add tests
5. Ensure all tests pass
6. Submit a pull request

### Code Style

- Use Black for code formatting: `black .`
- Use isort for import sorting: `isort .`
- Use flake8 for linting: `flake8 .`
- Use mypy for type checking: `mypy .`

### Testing Guidelines

- Write tests for all new endpoints
- Include both success and error cases
- Test authentication and authorization
- Test rate limiting behavior
- Update the test suite in `test_comprehensive_api.py`

## 📞 Support

For questions or issues:

1. Check the API documentation: http://localhost:8000/docs
2. Run the test suite: `python run_api_tests.py`
3. Check the logs: `tail -f storysign_api.log`
4. Review this README and configuration

## 📄 License

This API implementation is part of the StorySign ASL Platform project.

---

**Happy coding! 🎉**
