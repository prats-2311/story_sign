# Unified Development Workflow

## 🎯 **Problem Solved:**

- ✅ **One codebase** for both local and production
- ✅ **No more sync issues** between different files
- ✅ **Same features everywhere** - what works locally works in production
- ✅ **Easy bug fixes** - fix once, works everywhere

## 🔧 **How It Works:**

### **Single File: `main_api_production.py`**

- **Auto-detects environment** (local vs production)
- **Same authentication system** (real TiDB database)
- **Same AI services** (Groq + Ollama)
- **Environment-aware settings** (CORS, logging, etc.)

### **Environment Detection:**

```python
# Automatic detection
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production" or os.getenv("RENDER") is not None
IS_LOCAL = not IS_PRODUCTION

# Different settings per environment
if IS_PRODUCTION:
    cors_origins = ["https://storysign-platform.netlify.app"]  # Restrictive
else:
    cors_origins = ["*"]  # Permissive for local dev
```

## 🚀 **Development Workflow:**

### **1. Local Development:**

```bash
cd StorySign_Platform/backend

# Option A: Direct run
python main_api_production.py --reload

# Option B: Using dev script
python dev.py

# Option C: Custom settings
python main_api_production.py --host 127.0.0.1 --port 8080 --reload
```

### **2. Production Deployment:**

```bash
# render.yaml automatically uses:
startCommand: "cd StorySign_Platform/backend && python main_api_production.py"

# No changes needed - same file!
```

## 📊 **What You Get:**

### **Local Development:**

```
🔧 Running in LOCAL DEVELOPMENT mode
🔓 Using local development CORS settings
📍 Local URL: http://127.0.0.1:8000
📚 API Docs: http://127.0.0.1:8000/docs
🔄 Auto-reload: Enabled
✅ Database authentication loaded (REAL DATA)
✅ ASL World module loaded (includes Groq + Ollama)
```

### **Production:**

```
🚀 Running in PRODUCTION mode (Render)
🔒 Using production CORS settings
✅ Database authentication loaded (REAL DATA)
✅ ASL World module loaded (includes Groq + Ollama)
```

## 🔄 **Adding New Features:**

### **Step 1: Develop Locally**

```bash
cd StorySign_Platform/backend
python dev.py  # Uses main_api_production.py

# Make your changes to:
# - API endpoints in api/
# - Services in services/
# - Models in models/
# - etc.

# Test locally with real data
curl http://127.0.0.1:8000/api/v1/auth/login
curl http://127.0.0.1:8000/api/asl-world/story/recognize_and_generate
```

### **Step 2: Deploy to Production**

```bash
git add .
git commit -m "Add new feature X"
git push origin main

# Render automatically deploys the SAME file
# No sync issues, no separate production code
```

### **Step 3: Verify Production**

```bash
# Same endpoints work in production
curl https://story-sign.onrender.com/api/v1/auth/login
curl https://story-sign.onrender.com/api/asl-world/story/recognize_and_generate
```

## 🛠️ **Bug Fixing Workflow:**

### **Scenario: Login not working**

1. **Reproduce locally:**

   ```bash
   python dev.py
   # Test login at http://127.0.0.1:8000/docs
   ```

2. **Fix the issue:**

   ```bash
   # Edit api/auth_db.py or wherever the bug is
   # Auto-reload shows changes immediately
   ```

3. **Test fix locally:**

   ```bash
   # Verify fix works with real data
   curl -X POST http://127.0.0.1:8000/api/v1/auth/login -d '...'
   ```

4. **Deploy fix:**
   ```bash
   git add .
   git commit -m "Fix login issue"
   git push origin main
   # Same fix automatically works in production
   ```

## 📋 **Environment Variables:**

### **Local (.env file):**

```bash
# StorySign_Platform/backend/.env
GROQ_API_KEY=your_groq_key
JWT_SECRET=your_jwt_secret
DATABASE_HOST=your_tidb_host
DATABASE_USER=your_tidb_user
DATABASE_PASSWORD=your_tidb_password
ENVIRONMENT=development  # Optional, auto-detected
```

### **Production (Render Dashboard):**

```bash
GROQ_API_KEY=your_groq_key
JWT_SECRET=your_jwt_secret
DATABASE_HOST=your_tidb_host
DATABASE_USER=your_tidb_user
DATABASE_PASSWORD=your_tidb_password
ENVIRONMENT=production  # Set by Render
RENDER=true  # Set by Render
```

## 🔍 **Testing Both Environments:**

### **Local Testing:**

```bash
# Start local server
python dev.py

# Test endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/  # Shows "Local Development"
```

### **Production Testing:**

```bash
# After deployment
curl https://story-sign.onrender.com/health
curl https://story-sign.onrender.com/  # Shows "Production (Render)"
```

## ✅ **Benefits:**

1. **No Code Duplication** - One file, two environments
2. **No Sync Issues** - Changes apply everywhere
3. **Real Data Everywhere** - Same database, same services
4. **Easy Debugging** - Reproduce production issues locally
5. **Consistent Behavior** - Same logic, same results
6. **Simple Deployment** - No file switching needed

## 🚨 **Important Notes:**

- **Always test locally first** before pushing to production
- **Use environment variables** for sensitive data (API keys, passwords)
- **The same database** is used locally and in production (be careful with test data)
- **Auto-reload only works locally** (production restarts on deploy)

---

**Status**: ✅ Unified workflow implemented  
**Local**: `python dev.py` or `python main_api_production.py --reload`  
**Production**: Automatic deployment of same file  
**Result**: One codebase, consistent behavior everywhere
