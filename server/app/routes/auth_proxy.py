import httpx
import logging
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth-proxy"])

class AuthProxy:
    def __init__(self):
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def proxy_request(self, request: Request, path: str):
        """Proxy request to auth service"""
        try:
            url = f"{self.auth_service_url}/auth{path}"
            logger.debug(f"Proxying request to: {url}")

            # Forward headers (excluding host)
            headers = dict(request.headers)
            headers.pop("host", None)

            # Extract cookies from request and forward them
            cookies = {}
            if request.headers.get("cookie"):
                cookie_header = request.headers.get("cookie")
                for cookie in cookie_header.split(";"):
                    if "=" in cookie:
                        name, value = cookie.strip().split("=", 1)
                        cookies[name] = value

            # Handle different HTTP methods
            if request.method == "GET":
                # For GET requests, forward query parameters
                params = dict(request.query_params)
                response = await self.client.get(url, params=params, headers=headers, cookies=cookies, follow_redirects=False)
            elif request.method == "POST":
                # For POST requests, forward body
                body = await request.body()
                response = await self.client.post(url, content=body, headers=headers, cookies=cookies, follow_redirects=False)
            else:
                # For other methods
                response = await self.client.request(
                    request.method, url, headers=headers, cookies=cookies, follow_redirects=False
                )

            logger.debug(f"Auth service response status: {response.status_code}")

            # Handle redirects
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if location:
                    logger.debug(f"Redirecting to: {location}")
                    redirect_response = RedirectResponse(location, status_code=response.status_code)
                    # Forward set-cookie headers from auth service
                    if "set-cookie" in response.headers:
                        redirect_response.headers["set-cookie"] = response.headers["set-cookie"]
                    # Forward X-Auth-Token header (for OAuth callback)
                    if "x-auth-token" in response.headers:
                        redirect_response.headers["x-auth-token"] = response.headers["x-auth-token"]
                        logger.debug("Forwarded X-Auth-Token header")
                    return redirect_response

            # Forward response with cookies
            if response.headers.get("content-type", "").startswith("application/json"):
                json_response = JSONResponse(content=response.json(), status_code=response.status_code)
                # Forward any set-cookie headers from auth service
                if "set-cookie" in response.headers:
                    json_response.headers["set-cookie"] = response.headers["set-cookie"]
                return json_response
            else:
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

        except Exception as e:
            logger.error(f"Auth proxy error: {str(e)}")
            raise HTTPException(status_code=503, detail="Auth service unavailable")

# Global auth proxy instance
auth_proxy = AuthProxy()

@router.get("/login")
async def login(request: Request):
    """Proxy OAuth login to auth service"""
    return await auth_proxy.proxy_request(request, "/login")

@router.get("/callback")
async def callback(request: Request):
    """Proxy OAuth callback to auth service"""
    return await auth_proxy.proxy_request(request, "/callback")

@router.post("/verify")
async def verify(request: Request):
    """Proxy auth verification to auth service"""
    return await auth_proxy.proxy_request(request, "/verify")

@router.post("/refresh")
async def refresh(request: Request):
    """Proxy token refresh to auth service"""
    return await auth_proxy.proxy_request(request, "/refresh")

@router.post("/logout")
async def logout_post(request: Request):
    """Proxy logout to auth service (POST)"""
    return await auth_proxy.proxy_request(request, "/logout")

@router.get("/logout")
async def logout_get(request: Request):
    """Proxy logout to auth service (GET)"""
    return await auth_proxy.proxy_request(request, "/logout")

@router.get("/me")
async def get_me(request: Request):
    """Proxy get current user to auth service"""
    return await auth_proxy.proxy_request(request, "/me")
