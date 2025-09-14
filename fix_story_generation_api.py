#!/usr/bin/env python3
"""
Fix story generation API path mismatch
"""

import os
import subprocess

def test_api_endpoints():
    """Test if both versioned and non-versioned endpoints exist"""
    print("🧪 Testing API endpoints...")
    
    api_file = "StorySign_Platform/backend/main_api_simple.py"
    
    try:
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check for both versioned and non-versioned endpoints
        required_endpoints = [
            # Versioned endpoints
            "@app.post(\"/api/v1/asl-world/story/recognize_and_generate\")",
            "@app.post(\"/api/v1/asl-world/story/generate\")",
            # Non-versioned endpoints (what frontend calls)
            "@app.post(\"/api/asl-world/story/recognize_and_generate\")",
            "@app.post(\"/api/asl-world/story/generate\")"
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint in content:
                print(f"✅ Found: {endpoint}")
            else:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print("❌ Missing endpoints:")
            for endpoint in missing_endpoints:
                print(f"   - {endpoint}")
            return False
        
        print("✅ All required endpoints present (both versioned and non-versioned)")
        return True
        
    except Exception as e:
        print(f"❌ Error reading API file: {e}")
        return False

def test_import():
    """Test if the updated API can be imported"""
    print("📦 Testing API import...")
    
    try:
        import sys
        original_dir = os.getcwd()
        os.chdir("StorySign_Platform/backend")
        sys.path.insert(0, '.')
        
        try:
            from main_api_simple import app
            print("✅ Updated API imports successfully")
            
            # Check if app has the new routes
            routes = [route.path for route in app.routes if hasattr(route, 'path')]
            
            # Check for the specific route the frontend is calling
            frontend_route = "/api/asl-world/story/recognize_and_generate"
            if frontend_route in routes:
                print(f"✅ Frontend route available: {frontend_route}")
            else:
                print(f"❌ Frontend route missing: {frontend_route}")
                print("Available routes:")
                for route in routes:
                    if "asl-world" in route:
                        print(f"   - {route}")
                return False
            
            result = True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            result = False
        finally:
            os.chdir(original_dir)
            if '.' in sys.path:
                sys.path.remove('.')
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing import: {e}")
        return False

def add_to_git():
    """Add updated API to git"""
    print("📝 Adding updated API to Git...")
    
    try:
        subprocess.run(["git", "add", "StorySign_Platform/backend/main_api_simple.py"], check=True)
        print("✅ Added updated API to Git")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error adding to Git: {e}")
        return False

def create_test_commands():
    """Create test commands for the fixed endpoints"""
    print("🧪 Creating test commands...")
    
    test_commands = """# Test Commands for Fixed Story Generation API

## Test the exact endpoint the frontend calls:

```bash
# Test story generation (non-versioned - what frontend uses)
curl -X POST https://story-sign.onrender.com/api/asl-world/story/recognize_and_generate \\
  -H "Content-Type: application/json" \\
  -d '{"frame_data": "data:image/jpeg;base64,test-image-data"}'

# Test story generation (versioned)
curl -X POST https://story-sign.onrender.com/api/v1/asl-world/story/recognize_and_generate \\
  -H "Content-Type: application/json" \\
  -d '{"frame_data": "data:image/jpeg;base64,test-image-data"}'
```

## Expected Response:

```json
{
  "success": true,
  "recognized_objects": ["book", "table", "lamp", "chair"],
  "story": {
    "id": 2,
    "title": "My Scanned Objects Story",
    "content": "I used my camera to scan the objects around me...",
    "sentences": [
      "I see a book on the table.",
      "The table is brown and sturdy.",
      "The lamp gives bright light.",
      "I sit on the comfortable chair."
    ],
    "vocabulary": ["book", "table", "lamp", "chair", "see", "brown", "light", "sit"]
  },
  "message": "Objects recognized and story generated from your scan (demo mode)"
}
```

## Frontend Integration:

After deployment, the frontend call:
```javascript
fetch(`${API_BASE_URL}/api/asl-world/story/recognize_and_generate`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ frame_data: imageData })
})
```

Should now work without 404 errors!
"""
    
    with open("STORY_GENERATION_API_TESTS.md", "w") as f:
        f.write(test_commands)
    
    print("✅ Created STORY_GENERATION_API_TESTS.md")
    return True

def main():
    """Run all fixes and tests"""
    print("🚀 Fixing Story Generation API Path Mismatch")
    print("=" * 50)
    
    fixes = [
        ("Test API endpoints", test_api_endpoints),
        ("Test API import", test_import),
        ("Add to Git", add_to_git),
        ("Create test commands", create_test_commands)
    ]
    
    results = []
    for fix_name, fix_func in fixes:
        print(f"\n{fix_name}:")
        print("-" * 30)
        result = fix_func()
        results.append((fix_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Fix Results:")
    
    all_passed = True
    for fix_name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"   {status} - {fix_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Story generation API path mismatch fixed!")
        print("\n📝 Next steps:")
        print("1. Commit the API fix:")
        print("   git commit -m 'Fix story generation API: add non-versioned endpoints for frontend compatibility'")
        print("   git push origin main")
        print("\n2. Wait for Render to redeploy")
        print("3. Test story generation from scan - should work without 404!")
        print("\n✅ Frontend will now successfully call the story generation API!")
    else:
        print("❌ Some fixes failed. Check the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())