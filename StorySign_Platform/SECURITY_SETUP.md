# Security Setup Guide

## 🔒 **Environment Variables Protection**

All `.env` files are now protected in `.gitignore` to prevent accidental exposure of sensitive information.

## 📋 **Setup Instructions:**

### **1. Backend Environment Setup:**

```bash
cd StorySign_Platform/backend

# Copy the template
cp .env.example .env

# Edit with your real values
nano .env  # or use your preferred editor
```

### **2. Frontend Environment Setup:**

```bash
cd StorySign_Platform/frontend

# Copy the template
cp .env.example .env

# Edit with your real values
nano .env  # or use your preferred editor
```

## 🔑 **Required API Keys:**

### **Groq API Key:**

1. Go to [https://console.groq.com/keys](https://console.groq.com/keys)
2. Create a new API key
3. Add to `backend/.env`: `GROQ_API_KEY=your_actual_key_here`

### **TiDB Database Credentials:**

1. Get from your TiDB Cloud dashboard
2. Add to `backend/.env`:
   ```
   DATABASE_HOST=your-tidb-host
   DATABASE_USER=your-tidb-user
   DATABASE_PASSWORD=your-tidb-password
   ```

### **JWT Secret:**

1. Generate a secure random string
2. Add to `backend/.env`: `JWT_SECRET=your-secure-random-string`

## 🛡️ **Security Best Practices:**

### **✅ DO:**

- Use `.env.example` templates for documentation
- Generate strong, unique JWT secrets
- Use different API keys for development and production
- Regularly rotate API keys
- Keep `.env` files local only

### **❌ DON'T:**

- Commit `.env` files to git
- Share API keys in chat/email
- Use production keys in development
- Use weak JWT secrets
- Store credentials in code

## 🔍 **Verify Protection:**

### **Check Git Status:**

```bash
git status
# .env files should NOT appear in the list
```

### **Test Ignore:**

```bash
# Make a change to .env file
echo "TEST=123" >> backend/.env

# Check git status again
git status
# Should still not show .env files
```

## 🚨 **If You Accidentally Committed Secrets:**

### **1. Remove from Git History:**

```bash
# Remove file from git but keep locally
git rm --cached backend/.env
git rm --cached frontend/.env

# Commit the removal
git commit -m "Remove .env files from tracking"

# Push to remove from remote
git push origin main
```

### **2. Rotate Compromised Keys:**

- Generate new Groq API key
- Generate new JWT secret
- Update production environment variables

## 📁 **Protected Files:**

The `.gitignore` now protects:

- `.env` (all variations)
- `.env.*` (any .env with suffix)
- `backend/.env*`
- `frontend/.env*`
- `mobile/.env*`
- API key files
- Certificate files
- Database dumps
- Backup files

## 🔧 **Development Workflow:**

### **New Developer Setup:**

1. Clone repository
2. Copy `.env.example` to `.env` in each directory
3. Get API keys from team lead
4. Fill in `.env` files with real values
5. Never commit `.env` files

### **Adding New Environment Variables:**

1. Add to `.env.example` with placeholder
2. Add to production environment (Render dashboard)
3. Update local `.env` with real value
4. Document in this guide

---

**Status**: 🔒 All environment files protected  
**Next**: Set up your local `.env` files using the templates
