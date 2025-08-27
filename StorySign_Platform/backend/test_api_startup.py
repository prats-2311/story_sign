#!/usr/bin/env python3
"""
Test API startup without complex dependencies
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test importing API modules"""
    print("🧪 Testing API module imports...")
    
    # Test core modules
    try:
        from api import system, asl_world, harmony, reconnect, websocket, services_demo
        print("✅ Core API modules imported successfully")
    except ImportError as e:
        print(f"❌ Core API modules failed: {e}")
        return False
    
    # Test new API modules
    try:
        from api import auth, users, documentation
        print("✅ New API modules imported successfully")
    except ImportError as e:
        print(f"⚠️  New API modules failed: {e}")
    
    # Test GraphQL
    try:
        from api.graphql_endpoint import graphql_app
        print("✅ GraphQL module imported successfully")
    except ImportError as e:
        print(f"⚠️  GraphQL module failed: {e}")
    
    # Test router
    try:
        from api.router import api_router
        print("✅ API router imported successfully")
        return True
    except ImportError as e:
        print(f"❌ API router failed: {e}")
        return False

def test_fastapi_app():
    """Test creating FastAPI app"""
    print("\n🚀 Testing FastAPI application creation...")
    
    try:
        from fastapi import FastAPI
        from api.router import api_router
        
        app = FastAPI(title="StorySign API Test")
        app.include_router(api_router)
        
        print("✅ FastAPI application created successfully")
        print(f"📊 Number of routes: {len(app.routes)}")
        
        # List some routes
        print("\n📋 Available routes:")
        for route in app.routes[:10]:  # Show first 10 routes
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = getattr(route, 'methods', set())
                if methods:
                    print(f"  {list(methods)[0]} {route.path}")
        
        if len(app.routes) > 10:
            print(f"  ... and {len(app.routes) - 10} more routes")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI application creation failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 StorySign API Startup Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ Import tests failed. Cannot proceed with FastAPI test.")
        return False
    
    # Test FastAPI app
    app_ok = test_fastapi_app()
    
    if app_ok:
        print("\n✅ All tests passed! API should start successfully.")
        print("\n📝 Next steps:")
        print("  1. Run: python main_api.py")
        print("  2. Visit: http://localhost:8000/docs")
        print("  3. Test: python run_api_tests.py")
        return True
    else:
        print("\n❌ FastAPI test failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)