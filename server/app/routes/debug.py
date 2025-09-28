from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import asyncio
import os
import sys
import aiohttp
from datetime import datetime

from ...agents.tools import get_service_token, save_recipe

router = APIRouter(prefix="/debug", tags=["debug"])

class MockRunContext:
    """Mock RunContext for testing tools without LiveKit agent"""
    def __init__(self):
        self.room = None
        self.agent = None

@router.get("/")
async def debug_home():
    """Debug tools home page"""
    return {
        "message": "Agent Debug Tools",
        "available_endpoints": {
            "GET /debug/env": "Check environment variables",
            "POST /debug/auth": "Test service authentication",
            "POST /debug/save-recipe": "Test save recipe tool",
            "GET /debug/connectivity": "Test API connectivity",
            "POST /debug/run-all": "Run all debug tests"
        },
        "usage": {
            "curl_auth": "curl -X POST http://localhost:8000/debug/auth",
            "curl_recipe": "curl -X POST http://localhost:8000/debug/save-recipe -H 'Content-Type: application/json' -d '{\"recipe_data\": \"Test recipe\"}'",
            "web_interface": "Visit http://localhost:8000/debug in browser for interactive testing"
        }
    }

@router.get("/env")
async def check_environment():
    """Check if required environment variables are set (without exposing values)"""
    required_vars = [
        "SERVICE_API_KEY",
        "AUTH_SERVICE_URL",
        "API_URL",
        "OPENAI_API_KEY",
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET"
    ]

    env_status = {}
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        is_set = bool(value and value.strip())
        env_status[var] = "✅ Set" if is_set else "❌ Missing"
        if not is_set:
            missing_vars.append(var)

    return {
        "environment_status": env_status,
        "all_required_set": len(missing_vars) == 0,
        "missing_variables": missing_vars,
        "total_checked": len(required_vars)
    }

@router.post("/auth")
async def test_service_auth():
    """Test service authentication"""
    start_time = datetime.now()

    # Clear cache for fresh test
    from ...agents import tools
    tools._service_token_cache = None

    try:
        token = await get_service_token()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if token:
            # Try to decode JWT for info (without verification)
            token_info = {"length": len(token), "preview": f"{token[:50]}..."}
            try:
                import jwt
                decoded = jwt.decode(token, options={"verify_signature": False})
                token_info["payload"] = decoded
            except:
                token_info["payload"] = "Could not decode (install PyJWT for details)"

            return {
                "success": True,
                "message": "Service authentication successful",
                "token_info": token_info,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Service authentication failed - no token received",
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            }

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        return {
            "success": False,
            "message": f"Service authentication error: {str(e)}",
            "duration_seconds": duration,
            "timestamp": end_time.isoformat()
        }

@router.post("/save-recipe")
async def test_save_recipe(request: Dict[str, Any] = {"recipe_data": "Debug test recipe"}):
    """Test save recipe tool"""
    start_time = datetime.now()

    try:
        # Create mock context
        context = MockRunContext()

        # Get recipe data from request
        recipe_data = request.get("recipe_data", "Debug test recipe from API")

        # Call save_recipe tool
        result = await save_recipe(context, recipe_data)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "success": bool(result and result.get("success")),
            "tool_result": result,
            "recipe_data_tested": recipe_data,
            "duration_seconds": duration,
            "timestamp": end_time.isoformat()
        }

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": duration,
            "timestamp": end_time.isoformat()
        }

@router.get("/connectivity")
async def test_connectivity():
    """Test connectivity to required services"""
    api_url = os.getenv("API_URL", "http://localhost:8000")
    auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

    tests = [
        ("main_api", f"{api_url}/health"),
        ("auth_service", f"{auth_service_url}/health"),
    ]

    results = {}

    for name, url in tests:
        start_time = datetime.now()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    if response.status == 200:
                        data = await response.json()
                        results[name] = {
                            "success": True,
                            "status_code": response.status,
                            "response": data,
                            "duration_seconds": duration,
                            "url": url
                        }
                    else:
                        results[name] = {
                            "success": False,
                            "status_code": response.status,
                            "duration_seconds": duration,
                            "url": url
                        }
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            results[name] = {
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "url": url
            }

    all_successful = all(result.get("success", False) for result in results.values())

    return {
        "overall_success": all_successful,
        "services": results,
        "summary": f"{sum(1 for r in results.values() if r.get('success'))} of {len(results)} services reachable"
    }

@router.post("/run-all")
async def run_all_tests():
    """Run all debug tests in sequence"""
    start_time = datetime.now()

    tests = []

    # Test 1: Environment
    env_result = await check_environment()
    tests.append(("environment", env_result))

    # Test 2: Connectivity
    conn_result = await test_connectivity()
    tests.append(("connectivity", conn_result))

    # Test 3: Authentication
    auth_result = await test_service_auth()
    tests.append(("authentication", auth_result))

    # Test 4: Save Recipe
    recipe_result = await test_save_recipe()
    tests.append(("save_recipe", recipe_result))

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    # Calculate summary
    passed_tests = sum(1 for name, result in tests if result.get("success", False))
    total_tests = len(tests)

    return {
        "overall_success": passed_tests == total_tests,
        "summary": f"{passed_tests}/{total_tests} tests passed",
        "total_duration_seconds": total_duration,
        "timestamp": end_time.isoformat(),
        "tests": {name: result for name, result in tests}
    }

# Create router function for main API
def create_debug_router():
    """Create debug router for main API"""
    return router