import datetime

import jwt
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import os
from typing import Optional
import httpx
import sys

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)])

if os.getenv("AUTH_DEBUG", "false").lower() == "true":
    logger.setLevel(logging.DEBUG)

# Config
JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# OAuth Setup
oauth = OAuth()

router = APIRouter(prefix="/auth", tags=["auth"])


def get_frontend_url(request: Request) -> str:
    """Get frontend URL from origin header"""
    origin = request.headers.get("origin")
    if origin:
        logger.debug(f"Frontend URL from origin: {origin}")
        return origin

    # Fallback to default for local development
    default_url = "http://localhost:3000"
    logger.debug(f"Using default frontend URL: {default_url}")
    return default_url


def create_jwt_token(user_data: dict) -> str:
    """Create JWT token"""
    payload = {
        "sub": user_data["email"],
        "email": user_data["email"],
        "name": user_data.get("name"),
        "picture": user_data.get("picture"),
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.debug("JWT token invalid")
        return None


@router.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login"""
    try:
        logger.info("OAuth login initiated")

        if not hasattr(oauth, 'google'):
            error_msg = (
                "Google OAuth is not configured. "
                "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            )
            logger.error("OAuth not configured")
            raise HTTPException(status_code=500, detail=error_msg)

        # Get frontend URL for OAuth redirect_uri (where Google sends users back)
        frontend_url = get_frontend_url(request)
        redirect_uri = f"{frontend_url}/auth/google/callback"
        logger.info(f"OAuth redirect_uri: {redirect_uri}")

        # Generate secure state parameter for CSRF protection
        import secrets
        state = secrets.token_urlsafe(32)

        # Store state in Redis for validation (with 10 minute expiry)
        if hasattr(request.app.state, 'redis'):
            await request.app.state.redis.setex(f"oauth_state:{state}", 600, state)
            logger.debug(f"Stored OAuth state in Redis: {state[:8]}...")
        else:
            # Fallback to session if Redis unavailable
            request.session["oauth_state"] = state
            logger.warning("Redis unavailable, using session for OAuth state")

        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth"
            f"?client_id={google_client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=openid email profile"
            f"&response_type=code"
            f"&access_type=offline"
            f"&state={state}"
        )

        logger.info("OAuth redirect generated")
        return RedirectResponse(auth_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login route: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request):
    """Handle OAuth callback and return JWT token"""
    logger.info("OAuth callback received")

    try:
        code = request.query_params.get('code')
        state = request.query_params.get('state')

        if not code:
            logger.error("No authorization code found in callback")
            raise HTTPException(status_code=400, detail="No authorization code received")

        # Validate state parameter for CSRF protection
        if not state:
            logger.error("No state parameter in OAuth callback")
            raise HTTPException(status_code=400, detail="Missing state parameter")

        # Check Redis first, fallback to session
        session_state = None
        if hasattr(request.app.state, 'redis'):
            session_state = await request.app.state.redis.get(f"oauth_state:{state}")
            if session_state:
                # Delete the state after validation (one-time use)
                await request.app.state.redis.delete(f"oauth_state:{state}")
                logger.debug("OAuth state validated via Redis")
        else:
            session_state = request.session.get("oauth_state")
            request.session.pop("oauth_state", None)
            logger.debug("OAuth state validated via session")

        if not session_state or session_state != state:
            logger.error("Invalid state parameter in OAuth callback")
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        logger.info("OAuth state validation successful")

        # CRITICAL: redirect_uri must match what we sent to Google in /auth/login
        frontend_url = get_frontend_url(request)
        redirect_uri = f"{frontend_url}/auth/google/callback"
        logger.info(f"Token exchange redirect_uri: {redirect_uri}")

        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_data = {
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_response.raise_for_status()
            token_result = token_response.json()

            access_token = token_result.get('access_token')
            if not access_token:
                logger.error("No access token in response")
                raise HTTPException(status_code=400, detail="No access token received")

            logger.info("Successfully exchanged code for access token")

            # Get user info using the access token
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers=headers
            )
            user_response.raise_for_status()
            user_info = user_response.json()

        user_email = user_info.get('email')
        logger.info(f"OAuth successful for user: {user_email[:3]}***@{user_email.split('@')[1] if '@' in user_email else 'unknown'}")

        user_data = {
            "email": user_info["email"],
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }

        # Create JWT token
        jwt_token = create_jwt_token(user_data)
        logger.info("JWT token generated successfully")

        # Return JWT in header for Next.js to set as cookie
        frontend_url = get_frontend_url(request)
        response = RedirectResponse(frontend_url, status_code=302)
        response.headers['X-Auth-Token'] = jwt_token
        logger.info("JWT token sent in X-Auth-Token header")

        return response

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during token exchange: {e}")
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/verify")
async def verify_auth(request: Request):
    """Verify JWT token"""
    try:
        # Try JWT from Authorization header
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split()[1]
            payload = verify_jwt_token(token)
            if payload:
                logger.debug(f"Verified via JWT header: {payload.get('email')}")
                return {"authenticated": True, "user": payload, "method": "jwt_header"}

        # Try JWT from cookie
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            payload = verify_jwt_token(token_cookie)
            if payload:
                logger.debug(f"Verified via JWT cookie: {payload.get('email')}")
                return {"authenticated": True, "user": payload, "method": "jwt_cookie"}

        # Try JWT from request body
        try:
            body = await request.json()
            token = body.get("token")
            if token:
                payload = verify_jwt_token(token)
                if payload:
                    logger.debug(f"Verified via JWT body: {payload.get('email')}")
                    return {"authenticated": True, "user": payload, "method": "jwt_body"}
        except:
            pass

        logger.debug("No valid authentication found")
        return {"authenticated": False}

    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        return {"authenticated": False, "error": str(e)}


@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh JWT token"""
    try:
        # Get current token from Authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        current_token = authorization.split()[1]
        payload = verify_jwt_token(current_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Create new token with same user data
        user_data = {
            "email": payload["email"],
            "name": payload.get("name"),
            "picture": payload.get("picture"),
        }

        new_token = create_jwt_token(user_data)
        logger.debug(f"JWT refreshed for: {user_data.get('email')}")

        return {"token": new_token, "user": user_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")


async def perform_logout(request: Request):
    """Common logout logic"""
    logger.info("Logout request received")

    # Get frontend URL for redirect
    frontend_url = get_frontend_url(request)

    # Just redirect - Next.js will handle cookie clearing
    response = RedirectResponse(frontend_url, status_code=302)
    logger.info("Logout redirect sent")

    return response

@router.post("/logout")
async def logout_post(request: Request):
    """Logout and clear JWT cookie (POST)"""
    return await perform_logout(request)

@router.get("/logout")
async def logout_get(request: Request):
    """Logout and clear JWT cookie (GET)"""
    return await perform_logout(request)


@router.get("/me")
async def get_me(request: Request):
    """Get current user information via JWT"""
    try:
        # Try JWT from Authorization header
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split()[1]
            payload = verify_jwt_token(token)
            if payload:
                logger.debug(f"User info retrieved via header: {payload.get('email')}")
                return {"authenticated": True, "user": payload}

        # Try JWT from cookie
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            payload = verify_jwt_token(token_cookie)
            if payload:
                logger.debug(f"User info retrieved via cookie: {payload.get('email')}")
                return {"authenticated": True, "user": payload}

        logger.info("No valid authentication found in /me request")
        return {"authenticated": False}

    except Exception as e:
        logger.error(f"Error in /me endpoint: {str(e)}")
        return {"authenticated": False, "error": str(e)}


@router.post("/service-auth")
async def service_auth(request: Request):
    """Authenticate a service using API key and return JWT token"""
    try:
        # Get API key from header
        api_key = request.headers.get("x-api-key")
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")

        # Validate API key against environment variable
        valid_service_key = os.getenv("SERVICE_API_KEY")
        if not valid_service_key:
            logger.error("SERVICE_API_KEY not configured")
            raise HTTPException(status_code=500, detail="Service authentication not configured")

        if api_key != valid_service_key:
            logger.warning("Invalid service API key attempted")
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Create service account user data
        service_user_data = {
            "email": "service@raimy.internal",
            "name": "Raimy Service Account",
            "picture": None,
            "service": True  # Mark as service account
        }

        # Create JWT token for service
        service_token = create_jwt_token(service_user_data)
        logger.info("Service token created for internal service")

        return {
            "token": service_token,
            "user": service_user_data,
            "type": "service_account"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in service authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service authentication failed: {str(e)}")
