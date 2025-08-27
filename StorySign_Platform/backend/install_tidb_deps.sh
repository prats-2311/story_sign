#!/bin/bash

# TiDB Dependencies Installation Script
# Installs the required MySQL drivers for TiDB connectivity

echo "🔧 Installing TiDB dependencies for StorySign..."
echo "================================================"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Consider activating one first."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

echo
echo "📦 Installing MySQL drivers for TiDB..."

# Install the required packages
pip install sqlalchemy[asyncio]>=2.0.0
pip install asyncmy>=0.2.9
pip install pymysql>=1.1.0
pip install mysql-connector-python>=8.0.0

echo
echo "✅ TiDB dependencies installed successfully!"
echo
echo "Next steps:"
echo "1. Update your config.yaml with TiDB connection details"
echo "2. Run: python run_migrations.py"
echo "3. Test connection: python test_tidb_connection.py"