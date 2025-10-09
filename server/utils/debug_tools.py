#!/usr/bin/env python3
"""
Debug tools for testing agent authentication and tools without running costly agent calls.

Usage:
  python debug_tools.py auth          # Test service authentication
  python debug_tools.py save-recipe   # Test save_recipe tool
  python debug_tools.py all           # Test all functions
"""

import asyncio
import sys
import os
import json
# Import from MCP server instead of agents.tools
from server.mcp_service.server import get_service_token, save_recipe


class MockRunContext:
    """Mock RunContext for testing tools without LiveKit agent"""
    def __init__(self):
        self.room = None
        self.agent = None

async def test_service_auth():
    """Test service authentication"""
    print("🧪 Testing Service Authentication")
    print("=" * 50)

    # Check environment variables
    print(f"SERVICE_API_KEY: {'✅ Set' if os.getenv('SERVICE_API_KEY') else '❌ Not set'}")
    print(f"AUTH_SERVICE_URL: {os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8001')}")
    print()

    # Clear cache for fresh test
    from server.mcp_service import server as mcp_server
    mcp_server._service_token_cache = None

    # Test authentication
    token = await get_service_token()

    if token:
        print(f"✅ SUCCESS: Got JWT token")
        print(f"Token length: {len(token)} characters")
        print(f"Token preview: {token[:50]}...")

        # Decode JWT to show contents (without verification)
        try:
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"Token payload: {json.dumps(decoded, indent=2)}")
        except ImportError:
            print("(Install PyJWT to see token contents)")
        except Exception as e:
            print(f"Could not decode token: {e}")
    else:
        print("❌ FAILED: Could not get JWT token")

    return token is not None

async def test_save_recipe():
    """Test save_recipe tool"""
    print("🧪 Testing Save Recipe Tool")
    print("=" * 50)

    # Create mock context
    context = MockRunContext()

    # Test recipe data
    test_recipe = "A delicious test recipe with ingredients and steps"

    print(f"Testing with recipe: {test_recipe}")
    print()

    # Call save_recipe tool
    result = await save_recipe(context, test_recipe)

    if result and result.get("success"):
        print("✅ SUCCESS: Recipe saved successfully")
        print(f"Recipe ID: {result.get('recipe_id')}")
        print(f"Message: {result.get('message')}")
    else:
        print("❌ FAILED: Recipe save failed")
        print(f"Result: {result}")

    return result is not None and result.get("success")

async def test_api_connection():
    """Test basic API connectivity"""
    print("🧪 Testing API Connection")
    print("=" * 50)

    import aiohttp

    api_url = os.getenv("API_URL", "http://localhost:8000")
    auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

    tests = [
        ("Main API Health", f"{api_url}/health"),
        ("Auth Service Health", f"{auth_service_url}/health"),
    ]

    results = []

    for name, url in tests:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {name}: {response.status} - {data}")
                        results.append(True)
                    else:
                        print(f"❌ {name}: {response.status}")
                        results.append(False)
        except Exception as e:
            print(f"❌ {name}: Connection failed - {e}")
            results.append(False)

    return all(results)

async def run_all_tests():
    """Run all debug tests"""
    print("🧪 Running All Debug Tests")
    print("=" * 60)
    print()

    tests = [
        ("API Connection", test_api_connection),
        ("Service Authentication", test_service_auth),
        ("Save Recipe Tool", test_save_recipe),
    ]

    results = []

    for name, test_func in tests:
        print(f"Running {name}...")
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
        print()

    # Summary
    print("📊 Test Summary")
    print("=" * 30)
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1

    print(f"\nPassed: {passed}/{len(results)} tests")

    if passed == len(results):
        print("🎉 All tests passed! Agent tools should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "auth":
        await test_service_auth()
    elif command == "save-recipe":
        await test_save_recipe()
    elif command == "api":
        await test_api_connection()
    elif command == "all":
        await run_all_tests()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    asyncio.run(main())