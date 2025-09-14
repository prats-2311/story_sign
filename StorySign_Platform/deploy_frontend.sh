#!/bin/bash

# Frontend Deployment Script for Netlify
echo "🚀 Deploying StorySign Frontend to Netlify..."

# Check if we're in the right directory
if [ ! -f "netlify.toml" ]; then
    echo "❌ Error: netlify.toml not found. Run this script from the StorySign_Platform directory."
    exit 1
fi

# Validate frontend structure
echo "📋 Validating frontend structure..."
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: frontend/package.json not found"
    exit 1
fi

if [ ! -d "frontend/src" ]; then
    echo "❌ Error: frontend/src directory not found"
    exit 1
fi

# Check if backend URL is configured
echo "🔧 Checking API configuration..."
if grep -q "127.0.0.1:8000" frontend/src/config/api.js; then
    echo "⚠️  Warning: API configuration still points to localhost"
    echo "   This has been updated to use environment variables"
fi

# Install dependencies and test build
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

if [ $? -ne 0 ]; then
    echo "❌ Error: npm install failed"
    exit 1
fi

# Test build
echo "🔨 Testing production build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Error: Build failed"
    exit 1
fi

echo "✅ Build successful!"
cd ..

echo "✅ Frontend validation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Push your code to GitHub"
echo "2. Connect your GitHub repo to Netlify"
echo "3. Configure build settings in Netlify:"
echo "   - Base directory: frontend"
echo "   - Build command: npm run build"
echo "   - Publish directory: frontend/build"
echo "4. Set environment variables in Netlify:"
echo "   - REACT_APP_API_URL=https://your-backend.onrender.com"
echo "   - REACT_APP_WS_URL=wss://your-backend.onrender.com"
echo "   - REACT_APP_ENVIRONMENT=production"
echo "   - REACT_APP_USE_PROXY=true"
echo "5. Deploy!"
echo ""
echo "🔗 Netlify will use this configuration:"
echo "   - Automatic proxy to backend API via netlify.toml"
echo "   - SPA routing support"
echo "   - Security headers"
echo "   - Asset optimization"