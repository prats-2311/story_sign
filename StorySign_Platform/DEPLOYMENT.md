# StorySign Platform Deployment Guide

This guide covers the complete deployment process for the StorySign ASL Platform, including CI/CD setup, environment configuration, and monitoring.

## 🏗️ Architecture Overview

The StorySign Platform uses a modern cloud-native architecture:

- **Frontend**: React SPA deployed on Netlify
- **Backend**: FastAPI application deployed on Render
- **Database**: TiDB Cloud (MySQL-compatible)
- **AI Services**: Groq API for vision processing
- **CI/CD**: GitHub Actions for automated testing and deployment

## 📋 Prerequisites

### Required Accounts

1. **GitHub** - Source code repository
2. **Netlify** - Frontend hosting
3. **Render** - Backend hosting
4. **TiDB Cloud** - Database hosting
5. **Groq** - AI API services

### Required Tools (for local development)

- Node.js 18+
- Python 3.11+
- Git

## 🚀 Deployment Process

### 1. Repository Setup

1. Fork or clone the repository
2. Ensure all deployment configuration files are present:
   - `render.yaml` - Render deployment configuration
   - `netlify.toml` - Netlify deployment configuration
   - `frontend/public/_redirects` - Netlify redirects
   - `.github/workflows/` - CI/CD workflows

### 2. Backend Deployment (Render)

#### Step 1: Create Render Account

1. Sign up at [render.com](https://render.com)
2. Connect your GitHub account

#### Step 2: Create Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: `storysign-backend`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api:app --bind 0.0.0.0:$PORT`

#### Step 3: Configure Environment Variables

Set these environment variables in Render:

```bash
# Database Configuration
DATABASE_HOST=your-tidb-host
DATABASE_PORT=4000
DATABASE_NAME=storysign
DATABASE_USER=your-username
DATABASE_PASSWORD=your-password

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AI Services
GROQ_API_KEY=your-groq-api-key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL_NAME=llama-3.2-11b-vision-preview

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

#### Step 4: Deploy

1. Click "Create Web Service"
2. Wait for deployment to complete
3. Test the health endpoint: `https://your-app.onrender.com/health`

### 3. Frontend Deployment (Netlify)

#### Step 1: Create Netlify Account

1. Sign up at [netlify.com](https://netlify.com)
2. Connect your GitHub account

#### Step 2: Create Site

1. Click "Add new site" → "Import an existing project"
2. Choose GitHub and select your repository
3. Configure build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/build`

#### Step 3: Configure Environment Variables

Set these environment variables in Netlify:

```bash
# API Configuration
REACT_APP_API_URL=https://your-render-app.onrender.com
REACT_APP_WS_URL=wss://your-render-app.onrender.com
REACT_APP_API_VERSION=v1
REACT_APP_USE_PROXY=true
REACT_APP_ENVIRONMENT=production

# Build Configuration
GENERATE_SOURCEMAP=false
CI=true
NODE_VERSION=18
```

#### Step 4: Deploy

1. Click "Deploy site"
2. Wait for deployment to complete
3. Test the site: `https://your-site.netlify.app`

### 4. Database Setup (TiDB Cloud)

#### Step 1: Create TiDB Cloud Account

1. Sign up at [tidbcloud.com](https://tidbcloud.com)
2. Create a new cluster

#### Step 2: Configure Database

1. Create a database named `storysign`
2. Note the connection details
3. Configure firewall to allow Render's IP ranges

#### Step 3: Run Migrations

The backend will automatically create tables on first run, or you can run migrations manually:

```bash
cd backend
python run_migrations.py
```

## 🔧 CI/CD Configuration

### GitHub Secrets

Configure these secrets in your GitHub repository:

```bash
# Netlify
NETLIFY_AUTH_TOKEN=your-netlify-auth-token
NETLIFY_SITE_ID=your-netlify-site-id

# Render (optional, for webhook deployment)
RENDER_DEPLOY_HOOK=your-render-deploy-hook-url

# Notifications (optional)
SLACK_WEBHOOK_URL=your-slack-webhook-url

# Lighthouse CI (optional)
LHCI_GITHUB_APP_TOKEN=your-lighthouse-ci-token
```

### Workflow Overview

The CI/CD pipeline includes:

1. **Continuous Integration** (`ci.yml`)

   - Frontend and backend testing
   - Code quality checks
   - Security scanning
   - Build validation

2. **Deployment** (`deploy.yml`)

   - Automated deployment on main branch
   - Health checks
   - Rollback procedures

3. **Preview Deployments** (`preview.yml`)

   - Deploy PR previews
   - Accessibility testing
   - Performance monitoring

4. **Maintenance** (`maintenance.yml`)
   - Daily security audits
   - Dependency updates
   - Health monitoring

## 📊 Monitoring and Maintenance

### Health Checks

Both services include health check endpoints:

- **Backend**: `https://your-app.onrender.com/health`
- **Frontend**: Monitored via Netlify's built-in monitoring

### Automated Monitoring

The maintenance workflow runs daily and checks:

- Security vulnerabilities
- Dependency updates
- Service health
- Performance metrics

### Manual Monitoring

Regular checks you should perform:

1. **Weekly**:

   - Review deployment logs
   - Check error rates
   - Monitor performance metrics

2. **Monthly**:
   - Update dependencies
   - Review security reports
   - Optimize performance

## 🛠️ Troubleshooting

### Common Issues

#### Backend Deployment Fails

1. Check Render logs for error messages
2. Verify environment variables are set correctly
3. Ensure database connection is working
4. Check if all dependencies are in `requirements.txt`

#### Frontend Build Fails

1. Check Netlify build logs
2. Verify Node.js version (should be 18+)
3. Check for missing environment variables
4. Ensure all dependencies are in `package.json`

#### API Connection Issues

1. Verify CORS configuration
2. Check proxy settings in `netlify.toml`
3. Ensure backend is deployed and healthy
4. Verify environment variables match

### Debugging Commands

```bash
# Test backend locally
cd backend
python main_api.py

# Test frontend locally
cd frontend
npm start

# Check deployment configuration
./deploy.sh

# Validate configuration files
python -c "import yaml; yaml.safe_load(open('render.yaml'))"
```

## 🔒 Security Considerations

### Environment Variables

- Never commit secrets to version control
- Use strong, unique passwords
- Rotate API keys regularly
- Use different secrets for different environments

### HTTPS/SSL

- Both Netlify and Render provide automatic HTTPS
- Ensure all API calls use HTTPS in production
- Configure proper CORS headers

### Database Security

- Use strong database passwords
- Enable SSL connections
- Restrict database access to known IP ranges
- Regular security updates

## 📈 Performance Optimization

### Frontend

- Enable gzip compression (automatic on Netlify)
- Optimize images and assets
- Use code splitting
- Monitor Core Web Vitals

### Backend

- Use appropriate number of workers
- Enable database connection pooling
- Implement caching where appropriate
- Monitor response times

## 🆘 Support and Resources

### Documentation

- [Render Documentation](https://render.com/docs)
- [Netlify Documentation](https://docs.netlify.com)
- [TiDB Cloud Documentation](https://docs.pingcap.com/tidbcloud)
- [Groq API Documentation](https://console.groq.com/docs)

### Monitoring Tools

- Render Dashboard: https://dashboard.render.com
- Netlify Dashboard: https://app.netlify.com
- TiDB Cloud Console: https://tidbcloud.com

### Getting Help

1. Check the troubleshooting section above
2. Review deployment logs
3. Check GitHub Issues for similar problems
4. Contact support for the respective services

---

## 📝 Deployment Checklist

Use this checklist for each deployment:

### Pre-deployment

- [ ] All tests pass locally
- [ ] Code reviewed and approved
- [ ] Environment variables documented
- [ ] Database migrations ready (if any)
- [ ] Security scan completed

### Deployment

- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] Health checks pass
- [ ] Database migrations applied
- [ ] Environment variables configured

### Post-deployment

- [ ] Smoke tests completed
- [ ] Performance metrics checked
- [ ] Error monitoring active
- [ ] Team notified of deployment
- [ ] Documentation updated

---

_This deployment guide is maintained as part of the StorySign Platform documentation. Please keep it updated with any changes to the deployment process._
