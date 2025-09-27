import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
import os
from firebase_admin import firestore

logger = logging.getLogger(__name__)

class AuthClient:
    def __init__(self, auth_service_url: str = None):
        self.auth_service_url = auth_service_url or os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def verify_auth(self, request: Request) -> Dict[str, Any]:
        """Verify authentication via auth microservice"""
        try:
            # Prepare headers and cookies for auth service
            headers = {"content-type": "application/json"}

            # Get JWT token from Authorization header
            authorization = request.headers.get("authorization")
            if authorization and authorization.startswith("Bearer "):
                headers["authorization"] = authorization

            # Extract and forward cookies
            cookies = {}
            if request.headers.get("cookie"):
                cookie_header = request.headers.get("cookie")
                for cookie in cookie_header.split(";"):
                    if "=" in cookie:
                        name, value = cookie.strip().split("=", 1)
                        cookies[name] = value

            # Forward to auth service for verification
            response = await self.client.post(
                f"{self.auth_service_url}/auth/verify",
                headers=headers,
                cookies=cookies,
                json={}
            )

            if response.status_code == 200:
                auth_data = response.json()
                logger.debug(f"Auth verification result: {auth_data.get('authenticated')}")

                # If user is authenticated, store user data in Firestore
                if auth_data.get('authenticated') and auth_data.get('user'):
                    await self._store_user_data(auth_data['user'])

                return auth_data
            else:
                logger.error(f"Auth service error: {response.status_code}")
                return {"authenticated": False, "error": f"Auth service error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Failed to verify auth: {str(e)}")
            return {"authenticated": False, "error": str(e)}

    async def _store_user_data(self, user_data: Dict[str, Any]):
        """Store/update user data in Firestore"""
        try:
            db = firestore.client()
            user_email = user_data.get('email')
            if user_email:
                user_ref = db.collection("users").document(user_email)
                await user_ref.set({
                    **user_data,
                    "lastLogin": firestore.SERVER_TIMESTAMP
                }, merge=True)
                logger.debug(f"Updated user data for: {user_email}")
        except Exception as e:
            logger.warning(f"Failed to store user data: {str(e)}")  # Don't fail auth for storage issues

    async def get_current_user(self, request: Request) -> Dict[str, Any]:
        """Get current authenticated user or raise HTTPException"""
        auth_data = await self.verify_auth(request)

        if not auth_data.get("authenticated"):
            raise HTTPException(status_code=401, detail="Not authenticated")

        return auth_data.get("user", {})

    async def refresh_token(self, request: Request) -> Dict[str, Any]:
        """Refresh JWT token via auth service"""
        try:
            cookies = dict(request.cookies)
            headers = {
                "authorization": request.headers.get("authorization", ""),
                "cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()])
            }

            response = await self.client.post(
                f"{self.auth_service_url}/auth/refresh",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Token refresh failed")

        except httpx.RequestError as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise HTTPException(status_code=503, detail="Auth service unavailable")

    async def logout(self, request: Request) -> Dict[str, Any]:
        """Logout user via auth service"""
        try:
            cookies = dict(request.cookies)
            headers = {
                "authorization": request.headers.get("authorization", ""),
                "cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()])
            }

            response = await self.client.post(
                f"{self.auth_service_url}/auth/logout",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Logout failed: {response.status_code}")
                return {"status": "error", "detail": "Logout failed"}

        except Exception as e:
            logger.error(f"Failed to logout: {str(e)}")
            return {"status": "error", "detail": str(e)}

# Global auth client instance
auth_client = AuthClient()

# Dependency function for FastAPI
async def get_current_user(request: Request):
    """FastAPI dependency to get current user"""
    return await auth_client.get_current_user(request)

async def verify_auth_dependency(request: Request):
    """FastAPI dependency to verify authentication"""
    return await auth_client.verify_auth(request)