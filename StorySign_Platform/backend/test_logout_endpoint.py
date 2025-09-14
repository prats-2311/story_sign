#!/usr/bin/env python3
"""
Test the logout endpoint to verify it's working
"""

import asyncio
import aiohttp
import json

async def test_logout_endpoint():
    """Test the logout endpoint"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Logout Endpoint")
    print("="*40)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: POST to logout endpoint (should work now)
        print("1. Testing POST /api/v1/auth/logout")
        
        try:
            async with session.post(f"{base_url}/api/v1/auth/logout") as response:
                print(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Success: {data.get('message', 'No message')}")
                elif response.status == 404:
                    print(f"   ❌ 404 Not Found - Endpoint still missing")
                else:
                    error_text = await response.text()
                    print(f"   ⚠️  Status {response.status}: {error_text[:100]}")
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 2: Check if auth endpoints are available
        print("\n2. Testing auth endpoints availability")
        
        auth_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register", 
            "/api/v1/auth/logout",
            "/api/v1/auth/health"
        ]
        
        for endpoint in auth_endpoints:
            try:
                # Use OPTIONS to check if endpoint exists
                async with session.options(f"{base_url}{endpoint}") as response:
                    if response.status in [200, 405]:  # 405 = Method Not Allowed (but endpoint exists)
                        print(f"   ✅ {endpoint} - Available")
                    elif response.status == 404:
                        print(f"   ❌ {endpoint} - Not Found")
                    else:
                        print(f"   ⚠️  {endpoint} - Status {response.status}")
            except Exception as e:
                print(f"   ❌ {endpoint} - Exception: {e}")
        
        # Test 3: Check API documentation
        print("\n3. Testing API documentation")
        
        try:
            async with session.get(f"{base_url}/docs") as response:
                if response.status == 200:
                    print(f"   ✅ API docs available at {base_url}/docs")
                else:
                    print(f"   ⚠️  API docs status: {response.status}")
        except Exception as e:
            print(f"   ❌ API docs error: {e}")

async def main():
    """Main test function"""
    await test_logout_endpoint()
    
    print("\n" + "="*40)
    print("📋 Next Steps:")
    print("1. If logout endpoint is working: ✅ Issue resolved!")
    print("2. If still 404: Restart your backend server")
    print("3. Check API docs at http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    asyncio.run(main())