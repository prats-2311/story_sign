# Build Error Fix - Python 3.13 Compatibility

## 🔍 **Issue Identified:**

Build failed with Pillow 10.1.0 on Python 3.13:

```
KeyError: '__version__'
Getting requirements to build wheel did not run successfully
```

## 🛠️ **Root Cause:**

- **Python 3.13** compatibility issues with some packages
- **Pillow 10.1.0** doesn't build properly on Python 3.13
- **opencv-python** has complex build dependencies

## ✅ **Fix Applied:**

Created `requirements_minimal.txt` with only essential dependencies:

### ✅ **Included (Essential):**

- `fastapi` + `uvicorn` - Core API server
- `aiohttp` + `httpx` - For Groq API calls
- `pydantic[email]` + `email-validator` - For auth validation
- `bcrypt` + `pyjwt` + `passlib` - For authentication
- `sqlalchemy` - For database (auth)
- `groq` - For AI services
- `python-dotenv` + `pyyaml` - For configuration

### ❌ **Removed (Problematic):**

- `opencv-python` - Build issues on Python 3.13
- `pillow==10.1.0` - Version compatibility issues
- `numpy` - Not essential for core API
- `pymysql`, `asyncmy` - Extra database drivers
- `gunicorn`, `websockets` - Not essential for basic functionality

## 🎯 **Expected Result:**

This minimal set should:

- ✅ **Build successfully** on Python 3.13
- ✅ **Load auth module** (login endpoints work)
- ✅ **Load asl_world module** (story generation works)
- ✅ **Support Groq API** (vision processing works)

## 🚀 **Deploy Command:**

```bash
git add .
git commit -m "Fix build: use minimal requirements for Python 3.13 compatibility"
git push origin main
```

## 🔍 **Success Indicators:**

After deployment, logs should show:

```
✅ Successfully installed fastapi aiohttp pydantic bcrypt groq...
✅ ASL World module loaded (includes Groq + Ollama)
✅ Database authentication loaded
✅ Included asl_world router
✅ Included auth router
✅ Loaded modules: ['system', 'asl_world', 'auth']
```

## 📋 **Verification:**

```bash
# Should build without errors
curl https://story-sign.onrender.com/health

# Should show auth available
curl https://story-sign.onrender.com/health | jq '.services.authentication'

# Should not be 404
curl -X POST https://story-sign.onrender.com/api/v1/auth/login
```

---

**Status**: 🔧 Build compatibility fixed  
**Focus**: Core functionality (auth + story generation)  
**Trade-off**: Removed WebSocket/video features to ensure stable build
