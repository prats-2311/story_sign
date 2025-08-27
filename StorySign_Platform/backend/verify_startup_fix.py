#!/usr/bin/env python3
"""
Verify that the StorySign startup fix is working
"""

import sys
import time
from pathlib import Path

def test_main_import():
    """Test importing the main application"""
    print("🧪 Testing main application import...")
    try:
        import main
        print("✅ Main application imported successfully")
        return True
    except Exception as e:
        print(f"❌ Main application import failed: {e}")
        return False

def test_api_router():
    """Test API router functionality"""
    print("\n🧪 Testing API router...")
    try:
        from api.router import api_router
        route_count = len([r for r in api_router.routes])
        print(f"✅ API router imported successfully")
        print(f"📊 Available routes: {route_count}")
        return True
    except Exception as e:
        print(f"❌ API router import failed: {e}")
        return False

def test_fastapi_creation():
    """Test FastAPI application creation"""
    print("\n🧪 Testing FastAPI application creation...")
    try:
        from fastapi import FastAPI
        from api.router import api_router
        
        app = FastAPI(title="StorySign Test")
        app.include_router(api_router)
        
        print("✅ FastAPI application created successfully")
        print(f"📊 Total routes: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"❌ FastAPI application creation failed: {e}")
        return False

def test_key_endpoints():
    """Test that key endpoints are available"""
    print("\n🧪 Testing key endpoints...")
    try:
        from api.router import api_router
        
        # Check for key endpoints
        key_endpoints = [
            "/",
            "/config", 
            "/stats",
            "/api/asl-world/story/recognize_and_generate"
        ]
        
        available_paths = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                available_paths.append(route.path)
        
        found_endpoints = []
        for endpoint in key_endpoints:
            if endpoint in available_paths:
                found_endpoints.append(endpoint)
        
        print(f"✅ Key endpoints available: {len(found_endpoints)}/{len(key_endpoints)}")
        for endpoint in found_endpoints:
            print(f"  ✓ {endpoint}")
        
        return len(found_endpoints) >= 3  # At least 3 key endpoints should work
        
    except Exception as e:
        print(f"❌ Endpoint testing failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 StorySign Startup Fix Verification")
    print("=" * 50)
    
    tests = [
        ("Main Import", test_main_import),
        ("API Router", test_api_router),
        ("FastAPI Creation", test_fastapi_creation),
        ("Key Endpoints", test_key_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ StorySign startup fix is working correctly")
        print("\n🚀 Ready to start the application:")
        print("   python main.py")
        print("   or")
        print("   ./run_full_app.sh")
        print("\n📚 Documentation available at:")
        print("   http://localhost:8000/docs (when server is running)")
        
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("\n🔧 The application may have limited functionality")
        print("   Try installing missing dependencies:")
        print("   python install_missing_deps.py")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)