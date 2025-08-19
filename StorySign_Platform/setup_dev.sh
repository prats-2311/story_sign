#!/bin/bash

# StorySign Platform Development Setup Script

echo "🚀 Setting up StorySign Platform development environment..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed. Please install Miniconda or Anaconda first."
    echo "   Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup backend environment
echo "📦 Setting up backend environment..."
cd backend

if conda env list | grep -q "storysign-backend"; then
    echo "⚠️  Conda environment 'storysign-backend' already exists. Updating..."
    conda env update -f environment.yml
else
    echo "🔧 Creating new conda environment..."
    conda env create -f environment.yml
fi

echo "✅ Backend environment ready"

# Setup frontend dependencies
echo "📦 Setting up frontend dependencies..."
cd ../frontend

if [ -d "node_modules" ]; then
    echo "⚠️  node_modules already exists. Running npm install to update..."
fi

npm install

echo "✅ Frontend dependencies installed"

# Return to root directory
cd ..

# Initialize Git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "🔧 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Project structure and development environment setup"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "1. Backend: cd backend && conda activate storysign-backend && python dev_server.py"
echo "2. Frontend: cd frontend && npm run electron-dev"
echo ""
echo "The backend will run on http://localhost:8000"
echo "The frontend will open as a desktop application"
echo ""
echo "Git repository is ready for version control!"
echo "Next steps:"
echo "- Add your remote repository: git remote add origin <your-repo-url>"
echo "- Push to remote: git push -u origin main"