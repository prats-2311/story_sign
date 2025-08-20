#!/bin/bash

# StorySign Full Application Launcher
# Runs both backend (with MediaPipe) and frontend simultaneously

set -e  # Exit on any error

echo "🚀 Starting StorySign Full Application..."
echo "📍 Using mediapipe_env conda environment for backend"
echo "📍 Using npm for frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down StorySign application...${NC}"
    
    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${YELLOW}📱 Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}🌐 Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on ports 8000 and 3000
    echo -e "${YELLOW}🧹 Cleaning up ports...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM EXIT

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Error: conda is not installed or not in PATH${NC}"
    exit 1
fi

# Check if mediapipe_env exists
if ! conda env list | grep -q "mediapipe_env"; then
    echo -e "${RED}❌ Error: mediapipe_env conda environment not found${NC}"
    echo -e "${YELLOW}💡 Please create the environment first:${NC}"
    echo -e "   conda create -n mediapipe_env python=3.9"
    echo -e "   conda activate mediapipe_env"
    echo -e "   pip install mediapipe fastapi uvicorn websockets opencv-python numpy"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Error: npm is not installed or not in PATH${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Please run this script from the StorySign_Platform directory${NC}"
    echo -e "${YELLOW}💡 Current directory should contain 'backend' and 'frontend' folders${NC}"
    exit 1
fi

# Kill any existing processes on ports 8000 and 3000
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start backend with MediaPipe environment
echo -e "${BLUE}🔧 Starting backend with MediaPipe...${NC}"
cd backend
conda run -n mediapipe_env python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
sleep 5

# Test backend connectivity
echo -e "${BLUE}🔍 Testing backend connectivity...${NC}"
if curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✅ Backend is running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    exit 1
fi

# Install frontend dependencies if needed
echo -e "${BLUE}📦 Checking frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📥 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend
echo -e "${BLUE}🌐 Starting frontend...${NC}"
npm start &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo -e "${YELLOW}⏳ Waiting for frontend to start...${NC}"
sleep 10

echo -e "${GREEN}🎉 StorySign application is running!${NC}"
echo -e "${GREEN}📱 Backend: http://localhost:8000${NC}"
echo -e "${GREEN}🌐 Frontend: http://localhost:3000${NC}"
echo -e "${YELLOW}📋 Backend PID: $BACKEND_PID${NC}"
echo -e "${YELLOW}📋 Frontend PID: $FRONTEND_PID${NC}"
echo ""
echo -e "${BLUE}🎯 Instructions:${NC}"
echo -e "   1. Open http://localhost:3000 in your browser"
echo -e "   2. Click 'Test Backend' to verify connectivity"
echo -e "   3. Click 'Start Webcam' to enable camera"
echo -e "   4. Click 'Start Streaming' to see MediaPipe skeleton"
echo ""
echo -e "${YELLOW}⚠️  Press Ctrl+C to stop both services${NC}"

# Keep script running and wait for user interrupt
wait