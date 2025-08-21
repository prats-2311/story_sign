#!/bin/bash

echo "🚀 Starting StorySign with MediaPipe Environment"
echo "================================================"

# Check if mediapipe_env exists
if conda env list | grep -q "mediapipe_env"; then
    echo "✅ Found mediapipe_env environment"
else
    echo "❌ mediapipe_env environment not found"
    echo "Available environments:"
    conda env list
    exit 1
fi

# Function to start backend
start_backend() {
    echo "🔧 Starting backend with mediapipe_env..."
    cd backend
    
    # Activate mediapipe_env and start backend
    conda run -n mediapipe_env python main.py &
    BACKEND_PID=$!
    
    echo "✅ Backend started with PID: $BACKEND_PID"
    echo "🌐 Backend running at: http://localhost:8000"
    
    # Wait a moment for backend to start
    sleep 3
    
    # Test backend connection
    if curl -s http://localhost:8000/ > /dev/null; then
        echo "✅ Backend is responding"
    else
        echo "❌ Backend not responding"
        return 1
    fi
    
    cd ..
    return 0
}

# Function to start frontend
start_frontend() {
    echo "🔧 Starting frontend..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend
    npm start &
    FRONTEND_PID=$!
    
    echo "✅ Frontend started with PID: $FRONTEND_PID"
    echo "🌐 Frontend will open at: http://localhost:3000"
    
    cd ..
    return 0
}

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up processes..."
    pkill -f "python main.py"
    pkill -f "npm start"
    echo "✅ Cleanup completed"
}

# Set trap for cleanup on script exit
trap cleanup EXIT

# Main execution
echo "1. Starting backend..."
if start_backend; then
    echo "2. Starting frontend..."
    if start_frontend; then
        echo ""
        echo "🎉 StorySign is now running!"
        echo "📱 Open your browser to: http://localhost:3000"
        echo "🔧 Backend API available at: http://localhost:8000"
        echo ""
        echo "Press Ctrl+C to stop both services"
        
        # Wait for user interrupt
        while true; do
            sleep 1
        done
    else
        echo "❌ Failed to start frontend"
        exit 1
    fi
else
    echo "❌ Failed to start backend"
    exit 1
fi