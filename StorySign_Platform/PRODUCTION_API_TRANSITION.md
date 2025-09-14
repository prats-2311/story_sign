# StorySign Production API Transition Guide

## Overview

Successfully transitioned from `main_api_simple.py` (demo mode) to `main_api_production.py` (real AI services).

## What Changed

### From Simple API (Demo Mode):

- Static demo responses
- No real AI integration
- Basic health checks
- Minimal functionality

### To Production API (Real Services):

- **Groq Vision API** for object recognition
- **Ollama Cloud** for story generation
- **TiDB Cloud** database integration
- **JWT Authentication** with real user management
- **WebSocket** support for real-time features
- Comprehensive health monitoring

## Real Services Integration

### 1. Vision Processing (Groq)

- **Service**: Groq Vision API
- **Model**: `meta-llama/llama-4-scout-17b-16e-instruct`
- **Endpoint**: `/api/asl-world/story/recognize_and_generate`
- **Function**: Identifies objects from uploaded images

### 2. Story Generation (Ollama)

- **Service**: Ollama Cloud API
- **Model**: `gpt-oss:20b`
- **Function**: Generates 5-level stories (Amateur → Expert)
- **Output**: Structured JSON with titles, sentences, vocabulary

### 3. Database (TiDB Cloud)

- **Service**: TiDB Cloud (MySQL-compatible)
- **Function**: User data, stories, progress tracking
- **Authentication**: Real JWT with database backing

## Deployment Configuration

### Updated Files:

- ✅ `render.yaml` - Updated to use production API
- ✅ `main_api_production.py` - New production-ready API
- ✅ `deploy_production_api.py` - Validation script

### Environment Variables (Set in Render Dashboard):

```bash
# Required for Groq Vision
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct

# Required for Authentication
JWT_SECRET=your_secure_jwt_secret

# Required for Database
DATABASE_HOST=your_tidb_host
DATABASE_USER=your_tidb_user
DATABASE_PASSWORD=your_tidb_password

# Service Configuration
STORYSIGN_LOCAL_VISION__SERVICE_TYPE=groq
STORYSIGN_GROQ__ENABLED=true
```

## API Endpoints

### Core Endpoints:

- `GET /` - API information and status
- `GET /health` - Comprehensive health check
- `GET /docs` - Interactive API documentation

### Authentication:

- `POST /api/v1/auth/login` - User login with JWT
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/logout` - User logout

### ASL World (Main Feature):

- `POST /api/asl-world/story/recognize_and_generate` - **Main endpoint**
  - Accepts image data
  - Uses Groq to identify objects
  - Uses Ollama to generate stories
  - Returns structured story data

### WebSocket:

- `WS /ws/` - Real-time video processing

## Health Monitoring

The `/health` endpoint now provides comprehensive monitoring:

```json
{
  "status": "healthy|degraded|unhealthy",
  "services": {
    "groq_api": "healthy|unhealthy|not_configured",
    "ollama": "healthy|unhealthy|not_configured",
    "vision_service": "healthy|unhealthy|error",
    "story_service": "healthy|unhealthy|error",
    "authentication": "available|not_available",
    "environment": "healthy|missing_vars"
  }
}
```

## Testing the Production API

### 1. Health Check:

```bash
curl https://your-render-url.onrender.com/health
```

### 2. Story Generation:

```bash
curl -X POST https://your-render-url.onrender.com/api/asl-world/story/recognize_and_generate \
  -H "Content-Type: application/json" \
  -d '{"frame_data": "base64_image_data_here"}'
```

### 3. Authentication:

```bash
curl -X POST https://your-render-url.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

## Deployment Steps

### 1. Environment Variables:

Set these in your Render dashboard:

- `GROQ_API_KEY` - Your Groq API key
- `JWT_SECRET` - Secure random string
- `DATABASE_HOST`, `DATABASE_USER`, `DATABASE_PASSWORD` - TiDB credentials

### 2. Deploy:

```bash
git add .
git commit -m "Transition to production API with real AI services"
git push origin main
```

### 3. Monitor:

- Check Render logs for startup messages
- Test `/health` endpoint
- Verify AI services are working

## Expected Behavior

### Startup Logs:

```
StorySign Production API starting up...
Vision service (Groq): healthy
Story service (Ollama): healthy
StorySign Production API started successfully
```

### Story Generation Flow:

1. **Image Upload** → Frontend sends base64 image
2. **Object Recognition** → Groq Vision identifies objects
3. **Story Generation** → Ollama creates 5-level stories
4. **Response** → Structured JSON with stories

### Error Handling:

- Graceful fallbacks if services are unavailable
- Detailed error messages for debugging
- Retry logic for transient failures

## Troubleshooting

### Common Issues:

1. **Groq 401 Error**: Check `GROQ_API_KEY` in Render dashboard
2. **Ollama Connection**: Service should auto-connect to cloud
3. **Database Errors**: Verify TiDB credentials
4. **Import Errors**: Check all dependencies in `requirements.txt`

### Debug Commands:

```bash
# Test locally (with .env file)
python deploy_production_api.py

# Check specific service
python -c "from local_vision_service import get_vision_service; import asyncio; asyncio.run(get_vision_service().check_health())"
```

## Success Metrics

✅ **API starts successfully**  
✅ **Health endpoint returns 'healthy' or 'degraded'**  
✅ **Story generation works with real AI**  
✅ **Authentication functions properly**  
✅ **WebSocket connections work**

## Next Steps

1. **Monitor Performance**: Watch response times and error rates
2. **Scale Resources**: Upgrade Render plan if needed
3. **Add Features**: Implement additional AI capabilities
4. **Optimize**: Fine-tune AI model parameters
5. **Analytics**: Add usage tracking and metrics

---

**Status**: ✅ Ready for Production Deployment  
**Last Updated**: September 14, 2025  
**Version**: 1.0.0
