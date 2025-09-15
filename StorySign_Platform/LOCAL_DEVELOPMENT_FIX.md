# Local Development Fix Guide

## 🔍 **Issue Confirmed:**

The current source code is **broken for local development** due to missing database models. You're getting the same error as production:

```
ModuleNotFoundError: No module named 'models.progress'
```

## 🛠️ **Root Cause:**

- The `models/` directory is empty (no Python model files)
- `main.py` and `api.router` try to import ALL modules
- Some modules depend on database models that don't exist
- **No error handling** for missing dependencies

## ✅ **Solutions Provided:**

### 1. **Quick Fix - Use Local Development Server:**

```bash
cd StorySign_Platform/backend
python main_local.py
```

Or use the startup script:

```bash
python run_local.py
```

### 2. **What `main_local.py` Does:**

- ✅ **Safe module loading** with try/catch for each module
- ✅ **Only loads working modules** (system, asl_world, auth_simple)
- ✅ **Skips broken modules** gracefully
- ✅ **Shows which modules loaded** in logs and `/health` endpoint
- ✅ **Local development optimized** (CORS, reload, etc.)

## 📊 **Expected Local Startup:**

```
🚀 Starting StorySign Local Development API server
✅ System module loaded
✅ ASL World module loaded
✅ Auth Simple module loaded
❌ WebSocket module failed: No module named 'models.progress'
📍 URL: http://127.0.0.1:8000
📚 Docs: http://127.0.0.1:8000/docs
🔧 Working modules: ['system', 'asl_world', 'auth_simple']
```

## 🔍 **Available Endpoints (Local):**

- ✅ `GET /` - API information
- ✅ `GET /health` - Health check with working modules
- ✅ `GET /docs` - Interactive API documentation
- ✅ `POST /api/v1/auth/login` - Authentication (if auth_simple loads)
- ✅ `POST /api/asl-world/story/recognize_and_generate` - Story generation (if asl_world loads)

## 🚀 **Quick Start Commands:**

### Option 1: Direct Run

```bash
cd StorySign_Platform/backend
conda activate mediapipe_env  # or your venv
python main_local.py --reload
```

### Option 2: Using Startup Script

```bash
cd StorySign_Platform/backend
python run_local.py
```

### Option 3: Custom Port

```bash
python main_local.py --port 8080 --reload
```

## 🔧 **For Frontend Development:**

Update your frontend `.env` to point to the local server:

```bash
# StorySign_Platform/frontend/.env
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_WS_URL=ws://127.0.0.1:8000
REACT_APP_ENVIRONMENT=development
```

## 🛠️ **Alternative: Fix the Original main.py**

If you want to fix the original `main.py`, you'd need to either:

### Option A: Create Missing Models

```bash
# Create the missing model files
touch StorySign_Platform/backend/models/__init__.py
touch StorySign_Platform/backend/models/progress.py
# Then implement the actual model classes
```

### Option B: Modify api.router to Skip Broken Modules

```python
# In api/router.py, wrap imports in try/catch
try:
    from . import harmony
    api_router.include_router(harmony.router)
except ImportError:
    print("Harmony module skipped - missing dependencies")
```

## 📋 **Recommended Workflow:**

### For Local Development:

1. Use `main_local.py` for development
2. Test with working modules only
3. Focus on core functionality (auth + story generation)

### For Production:

1. Use `main_api_production.py` (already configured)
2. Handles missing dependencies gracefully
3. Provides same core functionality

## 🔍 **Verification:**

After starting the local server:

```bash
# Check health
curl http://127.0.0.1:8000/health

# Check working modules
curl http://127.0.0.1:8000/health | jq '.services.loaded_modules'

# Test auth endpoint
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

---

**Status**: ✅ Local development fixed  
**Solution**: Use `main_local.py` with safe module loading  
**Focus**: Core functionality (auth + story generation)
