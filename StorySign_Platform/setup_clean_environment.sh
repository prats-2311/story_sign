#!/bin/bash
# Clean Environment Setup for StorySign

echo "🧹 Setting up clean environment for StorySign..."

# Deactivate any virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Deactivating virtual environment: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

# Check if mediapipe_env exists
if conda env list | grep -q "mediapipe_env"; then
    echo "✅ mediapipe_env exists"
else
    echo "📦 Creating mediapipe_env with Python 3.10 (more compatible)..."
    conda create -n mediapipe_env python=3.10 -y
fi

# Activate mediapipe_env
echo "🔄 Activating mediapipe_env..."
conda activate mediapipe_env

# Verify environment
echo "🔍 Environment verification:"
echo "  Python: $(which python)"
echo "  Pip: $(which pip)"
echo "  Environment: $CONDA_DEFAULT_ENV"

# Install essential packages
echo "📦 Installing essential packages..."
pip install --upgrade pip setuptools wheel

# Install core packages one by one with error handling
packages=(
    "numpy>=1.21.0"
    "opencv-contrib-python>=4.8.0"
    "mediapipe==0.10.9"
    "fastapi>=0.100.0"
    "uvicorn>=0.23.0"
    "websockets>=11.0"
    "pydantic>=2.0.0"
    "PyYAML>=6.0"
    "psutil>=5.9.0"
)

for package in "${packages[@]}"; do
    echo "Installing $package..."
    if pip install "$package"; then
        echo "✅ $package installed successfully"
    else
        echo "❌ Failed to install $package"
    fi
done

echo "🎉 Clean environment setup complete!"
echo "Now run: python fix_environment.py"
