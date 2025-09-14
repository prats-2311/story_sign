#!/bin/bash

# Backend Deployment Script for Render
echo "🚀 Deploying StorySign Backend to Render..."

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Run this script from the StorySign_Platform directory."
    exit 1
fi

# Validate backend requirements
echo "📋 Validating backend requirements..."
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Error: backend/requirements.txt not found"
    exit 1
fi

if [ ! -f "backend/main_api.py" ]; then
    echo "❌ Error: backend/main_api.py not found"
    exit 1
fi

# Check environment variables
echo "🔧 Checking required environment variables..."
required_vars=(
    "DATABASE_HOST"
    "DATABASE_USER" 
    "DATABASE_PASSWORD"
    "JWT_SECRET"
    "GROQ_API_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "⚠️  Warning: The following environment variables are not set:"
    printf '   - %s\n' "${missing_vars[@]}"
    echo "   Make sure to set these in your Render dashboard."
fi

# Test backend startup locally (optional)
read -p "🧪 Test backend startup locally first? (y/n): " test_local
if [ "$test_local" = "y" ]; then
    echo "Testing backend startup..."
    cd backend
    python -c "
import sys
try:
    from main_api import app
    print('✅ Backend imports successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    cd ..
fi

echo "✅ Backend validation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Push your code to GitHub"
echo "2. Connect your GitHub repo to Render"
echo "3. Set environment variables in Render dashboard:"
echo "   - DATABASE_HOST (your TiDB Cloud host)"
echo "   - DATABASE_USER (your TiDB username)" 
echo "   - DATABASE_PASSWORD (your TiDB password)"
echo "   - JWT_SECRET (generate a secure secret)"
echo "   - GROQ_API_KEY (your Groq API key)"
echo "4. Deploy using the render.yaml configuration"
echo ""
echo "🔗 Render will use this configuration:"
echo "   Build Command: cd backend && pip install -r requirements.txt"
echo "   Start Command: cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api:app --bind 0.0.0.0:\$PORT"
echo "   Health Check: /health"