#!/bin/bash
# Start StorySign Backend with MediaPipe

echo "🚀 Starting StorySign Backend with MediaPipe..."
echo "📍 Activating storysign-mp environment..."

cd backend
conda activate storysign-mp
/opt/anaconda3/envs/storysign-mp/bin/python run_with_mediapipe.py