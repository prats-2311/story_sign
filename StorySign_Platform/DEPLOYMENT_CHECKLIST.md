# StorySign Platform Deployment Checklist

## 🎯 Architecture Overview

- **Frontend**: React SPA on Netlify (with proxy to backend)
- **Backend**: FastAPI on Render (handles all database operations)
- **Database**: TiDB Cloud (accessed only by backend)
- **Communication**: Frontend → Backend API → TiDB (NO direct frontend-to-database access)

## ✅ Pre-Deployment Checklist

### 1. Repository Setup

- [ ] Code pushed to GitHub
- [ ] All configuration files present:
  - [ ] `render.yaml` (backend deployment)
  - [ ] `netlify.toml` (frontend deployment)
  - [ ] `frontend/.env.production` (production environment)
  - [ ] `backend/requirements.txt` (Python dependencies)

### 2. TiDB Cloud Setup

- [ ] TiDB Cloud account created
- [ ] Database cluster created
- [ ] Database named `storysign` created
- [ ] Connection details noted:
  - [ ] Host (e.g., `gateway01.us-west-2.prod.aws.tidbcloud.com`)
  - [ ] Port (usually `4000`)
  - [ ] Username
  - [ ] Password
- [ ] Firewall configured to allow Render's IP ranges

### 3. External API Keys

- [ ] Groq API key obtained from https://console.groq.com/
- [ ] JWT secret generated (use: `openssl rand -hex 32`)

## 🚀 Deployment Steps

### Step 1: Deploy Backend to Render

1. **Create Render Account**

   - Sign up at https://render.com
   - Connect your GitHub account

2. **Create Web Service**

   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

3. **Configure Service**

   ```
   Name: storysign-backend
   Region: Oregon (US West)
   Branch: main
   Root Directory: (leave empty)
   Runtime: Python 3
   Build Command: cd backend && pip install -r requirements.txt
   Start Command: cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api:app --bind 0.0.0.0:$PORT --timeout 120
   ```

4. **Set Environment Variables**

   ```
   DATABASE_HOST=your-tidb-host.tidbcloud.com
   DATABASE_PORT=4000
   DATABASE_NAME=storysign
   DATABASE_USER=your-tidb-username
   DATABASE_PASSWORD=your-tidb-password
   JWT_SECRET=your-generated-jwt-secret
   GROQ_API_KEY=your-groq-api-key
   ENVIRONMENT=production
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note your backend URL (e.g., `https://storysign-backend.onrender.com`)

### Step 2: Deploy Frontend to Netlify

1. **Create Netlify Account**

   - Sign up at https://netlify.com
   - Connect your GitHub account

2. **Create Site**

   - Click "Add new site" → "Import an existing project"
   - Choose GitHub and select your repository

3. **Configure Build Settings**

   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/build
   ```

4. **Set Environment Variables**

   ```
   REACT_APP_API_URL=https://your-backend.onrender.com
   REACT_APP_WS_URL=wss://your-backend.onrender.com
   REACT_APP_ENVIRONMENT=production
   REACT_APP_USE_PROXY=true
   NODE_VERSION=18
   CI=true
   GENERATE_SOURCEMAP=false
   ```

5. **Deploy**
   - Click "Deploy site"
   - Wait for deployment to complete
   - Note your frontend URL (e.g., `https://storysign-platform.netlify.app`)

### Step 3: Update CORS Configuration

1. **Update Render Environment Variables**

   ```
   ALLOWED_ORIGINS=https://your-site.netlify.app,https://www.your-site.netlify.app
   ```

2. **Update Netlify Redirects**
   - The `netlify.toml` already configures proxy redirects
   - Update the backend URL in `netlify.toml` if needed

## 🧪 Testing Deployment

### Backend Health Check

```bash
curl https://your-backend.onrender.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "groq_api": "healthy",
    "authentication": "healthy"
  }
}
```

### Frontend API Connection

1. Open your Netlify site
2. Open browser developer tools
3. Check Network tab for API calls
4. Verify calls go to `/api/*` (proxied to backend)

### Database Connection

```bash
curl -X POST https://your-backend.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123","full_name":"Test User"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Backend fails to start**

   - Check Render logs for errors
   - Verify all environment variables are set
   - Check database connection

2. **Frontend can't connect to backend**

   - Verify CORS configuration
   - Check proxy settings in `netlify.toml`
   - Ensure environment variables are set correctly

3. **Database connection fails**
   - Verify TiDB Cloud credentials
   - Check firewall settings
   - Ensure SSL is properly configured

### Debug Commands

```bash
# Test backend locally
cd backend
python main_api.py

# Test frontend locally
cd frontend
npm start

# Check configuration
./deploy_backend.sh
./deploy_frontend.sh
```

## 🔒 Security Checklist

- [ ] JWT secret is strong and unique
- [ ] Database password is secure
- [ ] API keys are not committed to version control
- [ ] CORS is properly configured
- [ ] HTTPS is enabled (automatic on Render/Netlify)
- [ ] Environment variables are set correctly

## 📊 Monitoring

### Health Endpoints

- Backend: `https://your-backend.onrender.com/health`
- Metrics: `https://your-backend.onrender.com/metrics`

### Logs

- Render: Check deployment logs in Render dashboard
- Netlify: Check function logs and deploy logs
- TiDB: Monitor in TiDB Cloud console

## 🎉 Success Criteria

- [ ] Backend health check returns "healthy"
- [ ] Frontend loads without errors
- [ ] User registration/login works
- [ ] API calls are proxied correctly
- [ ] Database operations work through backend
- [ ] WebSocket connections establish successfully
- [ ] No direct frontend-to-database connections

## 📞 Support Resources

- [Render Documentation](https://render.com/docs)
- [Netlify Documentation](https://docs.netlify.com)
- [TiDB Cloud Documentation](https://docs.pingcap.com/tidbcloud)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)

---

**Important**: The frontend should NEVER connect directly to TiDB. All database operations must go through the backend API endpoints.
