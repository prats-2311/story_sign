# 🚨 Render Deployment - Immediate Fix Required

## ✅ Problem Identified

The error shows Render is trying to run:

```bash
cd backend && pip install -r requirements.txt
```

But it should be running:

```bash
cd StorySign_Platform/backend && pip install -r requirements_minimal.txt
```

**Root Cause**: Render dashboard has **manual build/start commands** that are overriding the `render.yaml` configuration.

## 🔧 Immediate Fix Steps

### Step 1: Check Render Dashboard Settings

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Find your service** (storysign-backend)
3. **Click on the service** to open it
4. **Go to Settings tab**

### Step 2: Clear Manual Overrides

Look for these fields and **clear them if they contain anything**:

**Build Command field**:

- If it shows: `cd backend && pip install -r requirements.txt` ❌
- **Clear it completely** (leave empty) ✅

**Start Command field**:

- If it shows: `cd backend && gunicorn ...` ❌
- **Clear it completely** (leave empty) ✅

**Root Directory**:

- Should be empty or `/` ✅

### Step 3: Verify Environment Variables

Ensure these are set in the Environment Variables section:

```
DATABASE_HOST=your-tidb-host
DATABASE_USER=your-tidb-username
DATABASE_PASSWORD=your-tidb-password
JWT_SECRET=your-generated-secret
ENVIRONMENT=production
```

### Step 4: Save and Redeploy

1. **Click "Save Changes"**
2. **Go to Deployments tab**
3. **Click "Manual Deploy"**
4. **Monitor the build logs**

## 🎯 Expected Success Result

After clearing the manual commands, Render should use `render.yaml` and show:

```
==> Running build command 'cd StorySign_Platform/backend && pip install -r requirements_minimal.txt'...
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 gunicorn-21.2.0 ...
==> Starting service with 'cd StorySign_Platform/backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api_simple:app'
==> Your service is live at https://your-backend.onrender.com
```

## 🔄 Alternative Solution: Create New Blueprint Service

If clearing the manual commands doesn't work:

### Option 1: Delete and Recreate

1. **Delete current service** in Render dashboard
2. **Create new service** using "Blueprint" option
3. **Connect to your GitHub repository**
4. **Render will automatically detect and use render.yaml**

### Option 2: Create Blueprint Service

1. **Go to Render dashboard**
2. **Click "New +" → "Blueprint"**
3. **Connect to GitHub repository**
4. **Select your repository**
5. **Render will use render.yaml automatically**

## 🧪 Test After Deployment

Once deployment succeeds, test the backend:

```bash
# Health check
curl https://your-backend.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-09-14T...",
  "services": {
    "api": "healthy",
    "cors": "healthy"
  }
}
```

## 📋 Why This Happened

When you initially created the Render service, you likely:

1. **Manually entered build/start commands** in the dashboard
2. **These manual settings take precedence** over render.yaml
3. **The manual commands had wrong paths** (backend instead of StorySign_Platform/backend)

## ✅ Success Criteria

- ✅ Build command uses correct path: `StorySign_Platform/backend`
- ✅ Uses minimal requirements: `requirements_minimal.txt`
- ✅ Uses simplified API: `main_api_simple:app`
- ✅ Service starts without directory errors
- ✅ Health endpoint returns "healthy"

---

**The fix is simple: Clear the manual build/start commands in Render dashboard to let it use render.yaml!** 🚀
