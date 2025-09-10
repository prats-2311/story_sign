#!/bin/bash

# StorySign Platform Deployment Script
# This script helps deploy the platform to Netlify and Render

set -e  # Exit on any error

echo "🚀 StorySign Platform Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "render.yaml" ] || [ ! -f "netlify.toml" ]; then
    print_error "Please run this script from the StorySign_Platform root directory"
    exit 1
fi

# Check for required tools
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18 or later."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    # Check Node version
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_warning "Node.js version is $NODE_VERSION. Recommended version is 18 or later."
    fi
    
    print_success "Dependencies check passed"
}

# Install frontend dependencies
install_frontend_deps() {
    print_status "Installing frontend dependencies..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        npm install
    else
        npm ci
    fi
    
    cd ..
    print_success "Frontend dependencies installed"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    cd frontend
    
    # Run linting
    print_status "Running ESLint..."
    npm run lint:ci || {
        print_warning "Linting issues found. Please fix them before deploying."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    
    # Run tests
    print_status "Running unit tests..."
    npm run test:ci || {
        print_warning "Some tests failed. Please fix them before deploying."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    
    cd ..
    print_success "Tests completed"
}

# Build frontend
build_frontend() {
    print_status "Building frontend for production..."
    cd frontend
    
    # Set production environment variables
    export REACT_APP_ENVIRONMENT=production
    export GENERATE_SOURCEMAP=false
    export CI=true
    
    npm run build:production
    
    cd ..
    print_success "Frontend build completed"
}

# Validate configuration
validate_config() {
    print_status "Validating deployment configuration..."
    
    # Check if required files exist
    if [ ! -f "render.yaml" ]; then
        print_error "render.yaml not found"
        exit 1
    fi
    
    if [ ! -f "netlify.toml" ]; then
        print_error "netlify.toml not found"
        exit 1
    fi
    
    if [ ! -f "frontend/public/_redirects" ]; then
        print_error "frontend/public/_redirects not found"
        exit 1
    fi
    
    # Check backend requirements
    if [ ! -f "backend/requirements.txt" ]; then
        print_error "backend/requirements.txt not found"
        exit 1
    fi
    
    # Check if Gunicorn is in requirements
    if ! grep -q "gunicorn" backend/requirements.txt; then
        print_error "Gunicorn not found in backend/requirements.txt"
        exit 1
    fi
    
    print_success "Configuration validation passed"
}

# Show deployment instructions
show_deployment_instructions() {
    echo
    echo "📋 Deployment Instructions"
    echo "=========================="
    echo
    echo "Backend (Render):"
    echo "1. Push your code to GitHub"
    echo "2. Connect your GitHub repository to Render"
    echo "3. Create a new Web Service with these settings:"
    echo "   - Build Command: cd backend && pip install -r requirements.txt"
    echo "   - Start Command: cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api:app --bind 0.0.0.0:\$PORT"
    echo "   - Health Check Path: /health"
    echo "4. Set the following environment variables in Render:"
    echo "   - DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD"
    echo "   - JWT_SECRET (generate a secure random string)"
    echo "   - GROQ_API_KEY (your Groq API key)"
    echo "   - ENVIRONMENT=production"
    echo
    echo "Frontend (Netlify):"
    echo "1. Push your code to GitHub"
    echo "2. Connect your GitHub repository to Netlify"
    echo "3. Set build settings:"
    echo "   - Base directory: frontend"
    echo "   - Build command: npm run build"
    echo "   - Publish directory: frontend/build"
    echo "4. Set environment variables:"
    echo "   - REACT_APP_API_URL=https://your-render-app.onrender.com"
    echo "   - REACT_APP_WS_URL=wss://your-render-app.onrender.com"
    echo "   - REACT_APP_USE_PROXY=true"
    echo "   - REACT_APP_ENVIRONMENT=production"
    echo
    echo "🔧 Configuration files created:"
    echo "- render.yaml (Render deployment configuration)"
    echo "- netlify.toml (Netlify deployment configuration)"
    echo "- frontend/public/_redirects (Netlify redirects)"
    echo "- frontend/.env.example (Environment variables template)"
    echo
}

# Main deployment flow
main() {
    echo "Select deployment option:"
    echo "1) Validate and prepare for deployment"
    echo "2) Build frontend only"
    echo "3) Run tests only"
    echo "4) Show deployment instructions"
    echo "5) Full preparation (validate + test + build)"
    echo
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            check_dependencies
            validate_config
            install_frontend_deps
            print_success "Ready for deployment!"
            ;;
        2)
            check_dependencies
            install_frontend_deps
            build_frontend
            ;;
        3)
            check_dependencies
            install_frontend_deps
            run_tests
            ;;
        4)
            show_deployment_instructions
            ;;
        5)
            check_dependencies
            validate_config
            install_frontend_deps
            run_tests
            build_frontend
            print_success "Full preparation completed!"
            show_deployment_instructions
            ;;
        *)
            print_error "Invalid choice. Please select 1-5."
            exit 1
            ;;
    esac
}

# Run main function
main