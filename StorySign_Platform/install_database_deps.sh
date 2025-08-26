#!/bin/bash

# Install database dependencies for StorySign Platform
# This script installs SQLAlchemy and TiDB drivers in the mediapipe_env

echo "🔧 Installing database dependencies for StorySign Platform..."

# Check if we're in the correct conda environment
if [[ "$CONDA_DEFAULT_ENV" != "mediapipe_env" ]]; then
    echo "⚠️  Warning: Not in mediapipe_env conda environment"
    echo "💡 Please run: conda activate mediapipe_env"
    echo "💡 Then run this script again"
    exit 1
fi

echo "✅ Using conda environment: $CONDA_DEFAULT_ENV"

# Install database dependencies
echo "📦 Installing SQLAlchemy with async support..."
pip install "sqlalchemy[asyncio]>=2.0.0"

echo "📦 Installing async MySQL driver for TiDB..."
pip install "asyncmy>=0.2.9"

echo "📦 Installing sync MySQL driver (fallback)..."
pip install "pymysql>=1.1.0"

echo "🧪 Testing database imports..."
python -c "
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    import asyncmy
    import pymysql
    print('✅ All database dependencies imported successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 Database dependencies installed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Start the application: ./run_full_app.sh"
    echo "2. The database service will now use full TiDB functionality"
    echo "3. Configure TiDB connection in backend/config.yaml if needed"
else
    echo "❌ Database dependency installation failed!"
    exit 1
fi