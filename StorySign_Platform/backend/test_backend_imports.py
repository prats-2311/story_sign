#!/usr/bin/env python3
"""
Test script to check what's failing in the backend imports
"""

import sys
import traceback

print("🔍 Testing Backend Module Imports")
print("=" * 50)

# Test basic imports
modules_to_test = [
    ("fastapi", "FastAPI"),
    ("aiohttp", "aiohttp"),
    ("config", "Configuration"),
    ("api.system", "System API"),
    ("api.auth_simple", "Simple Auth"),
    ("api.asl_world", "ASL World"),
    ("local_vision_service", "Vision Service"),
    ("ollama_service", "Ollama Service"),
]

for module_name, description in modules_to_test:
    try:
        __import__(module_name)
        print(f"✅ {description}: OK")
    except ImportError as e:
        print(f"❌ {description}: FAILED - {e}")
    except Exception as e:
        print(f"⚠️ {description}: ERROR - {e}")

print("\n🔍 Testing API Module Loading")
print("=" * 50)

try:
    from api import system
    print("✅ System module: OK")
    if hasattr(system, 'router'):
        print("✅ System router: OK")
    else:
        print("❌ System router: Missing")
except Exception as e:
    print(f"❌ System module: {e}")

try:
    from api import auth_simple
    print("✅ Auth simple module: OK")
    if hasattr(auth_simple, 'router'):
        print("✅ Auth router: OK")
    else:
        print("❌ Auth router: Missing")
except Exception as e:
    print(f"❌ Auth simple module: {e}")

try:
    from api import asl_world
    print("✅ ASL World module: OK")
    if hasattr(asl_world, 'router'):
        print("✅ ASL World router: OK")
    else:
        print("❌ ASL World router: Missing")
except Exception as e:
    print(f"❌ ASL World module: {e}")
    traceback.print_exc()

print("\n🔍 Testing Service Dependencies")
print("=" * 50)

try:
    from local_vision_service import get_vision_service
    print("✅ Vision service import: OK")
except Exception as e:
    print(f"❌ Vision service import: {e}")

try:
    from ollama_service import get_ollama_service
    print("✅ Ollama service import: OK")
except Exception as e:
    print(f"❌ Ollama service import: {e}")

print("\n📋 Summary")
print("=" * 50)
print("If any modules failed, the backend won't have those endpoints available.")
print("Check the error messages above to identify missing dependencies.")