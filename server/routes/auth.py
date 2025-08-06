import secrets
import datetime
import jwt
import logging
from fastapi import APIRouter, Request, Response, Depends, HTTPException, Header
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from itsdangerous import Signer
from firebase_admin import firestore
import os
from typing import Optional
import httpx
from datetime import timezone

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Default to INFO level

# Environment variable to control debug logging
if os.getenv("AUTH_DEBUG", "false").lower() == "true":
    logger.setLevel(logging.DEBUG)

# Initialize Firestore client (already initialized in your main app)
db = firestore.client()

# Config
SESSION_COOKIE_NAME = "sid"
SESSION_TTL = datetime.timedelta(days=7)
SIGNER_SECRET = os.getenv("SESSION_SIGNER_SECRET", "supersecret")  # rotate in prod
JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-key")  # rotate in prod
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
ACCESS_TOKEN_COOKIE_NAME = "access_token"

# Signer for cookies
signer = Signer(SIGNER_SECRET)

# OAuth Setup
oauth = OAuth()

# Global variables for dependency injection
broadcast_event_func = None

router = APIRouter(prefix="/auth", tags=["auth"])


# ----------------- Utility Functions -----------------

def get_frontend_url(request: Request) -> str:
    """Get frontend URL from request headers with fallbacks"""
    # Check referer header
    referer = request.headers.get("referer")
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        frontend_url = f"{parsed.scheme}://{parsed.netloc}"
        logger.debug(f"Frontend URL from referer: {frontend_url}")
        return frontend_url

    # Fallback to origin header
    origin = request.headers.get("origin")
    if origin:
        logger.debug(f"Frontend URL from origin: {origin}")
        return origin

    # Fallback to default localhost
    default_url = "http://localhost:3000"
    logger.debug(f"Using default frontend URL: {default_url}")
    return default_url


# ----------------- Session Helpers -----------------

def create_session(response: Response, user_data: dict):
    """Create Firestore session + set signed cookie + JWT token"""
    user_id = user_data["email"]
    user_ref = db.collection("users").document(user_id)
    user_ref.set({
        **user_data,
        "lastLogin": firestore.SERVER_TIMESTAMP
    }, merge=True)

    session_id = secrets.token_hex(32)
    db.collection("sessions").document(session_id).set({
        "user": user_ref,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "expiresAt": datetime.datetime.utcnow() + SESSION_TTL,
    })

    # Set session cookie
    signed = signer.sign(session_id.encode()).decode()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        signed,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",  # True in prod
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds())
    )

    # Create and set JWT token
    jwt_token = create_jwt_token(user_data)
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        jwt_token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",  # True in prod
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600
    )

    return session_id, jwt_token


def get_session(request: Request):
    """Return Firestore session doc or None"""
    logger.debug(f"get_session called - SESSION_COOKIE_NAME: {SESSION_COOKIE_NAME}")
    logger.debug(f"get_session called - All cookies: {dict(request.cookies)}")

    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        logger.debug("No session cookie found")
        return None

    try:
        session_id = signer.unsign(cookie.encode()).decode()
        logger.debug(f"Session ID extracted: {session_id[:8]}...")
    except Exception as e:
        logger.error(f"Failed to unsign session cookie: {e}")
        return None

    doc = db.collection("sessions").document(session_id).get()
    if not doc.exists:
        logger.debug("Session document not found in Firestore")
        return None

    session = doc.to_dict()
    logger.debug(f"Session found in Firestore: {session.keys() if session else 'None'}")

    # Expiration check
    if "expiresAt" in session:
        # Convert to timezone-aware datetime for comparison
        current_time = datetime.datetime.now(timezone.utc)
        expires_at = session["expiresAt"]

        if expires_at < current_time:
            logger.info("Session expired")
            db.collection("sessions").document(session_id).delete()
            return None

    logger.debug("Session valid and returned")
    return session


def clear_session(request: Request, response: Response):
    """Clear session from Firestore and cookies"""
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie:
        try:
            session_id = signer.unsign(cookie.encode()).decode()
            db.collection("sessions").document(session_id).delete()
        except Exception:
            pass

    # Clear both cookies
    response.delete_cookie(SESSION_COOKIE_NAME)
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)


# ----------------- JWT Helpers -----------------

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
        return None
    except jwt.InvalidTokenError:
        return None


# ----------------- Dependencies -----------------

async def get_current_user(request: Request):
    """Dependency to get current authenticated user (session-based)"""
    session = get_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_ref = session["user"]
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=401, detail="User not found")

    return user_doc.to_dict()


async def verify_jwt_header(authorization: str = Header(None)):
    """Dependency to verify JWT from Authorization header (stateless)"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split()[1]
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


async def get_current_user_jwt(user: dict = Depends(verify_jwt_header)):
    """Dependency to get current user from JWT (stateless)"""
    return user


async def get_current_user_flexible(request: Request):
    """Dependency that supports both session and JWT authentication"""
    # Try session first
    session = get_session(request)
    if session:
        user_ref = session["user"]
        user_doc = user_ref.get()
        if user_doc.exists:
            logger.debug(f"Authenticated via session: {user_doc.to_dict().get('email')}")
            return user_doc.to_dict()

    # Try JWT from Authorization header
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split()[1]
        payload = verify_jwt_token(token)
        if payload:
            logger.debug(f"Authenticated via JWT: {payload.get('email')}")
            return payload

    # Neither worked
    raise HTTPException(status_code=401, detail="Not authenticated")


# ----------------- SSE Integration for Logout -----------------

async def broadcast_logout_event(user_email: str):
    """Broadcast logout event via SSE"""
    if broadcast_event_func:
        await broadcast_event_func("user_logout", {"email": user_email})


# ----------------- Routes -----------------

@router.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login"""
    try:
        logger.info(f"OAuth login initiated - Referer: {request.headers.get('referer')}")

        # Check if OAuth is configured
        if not hasattr(oauth, 'google'):
            error_msg = (
                "Google OAuth is not configured. "
                "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables. "
                "You can get these from: https://console.cloud.google.com/apis/credentials"
            )
            logger.error(f"OAuth not configured: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        # Get frontend URL from request headers
        frontend_url = get_frontend_url(request)

        # Set redirect URI to client callback (which gets proxied to FastAPI)
        redirect_uri = f"{frontend_url}/auth/callback"
        logger.debug(f"Redirect URI: {redirect_uri}")
        logger.debug(f"This URI must be configured in Google Cloud Console OAuth settings")

        # Store redirect URI in session for callback
        if hasattr(request, 'session'):
            request.session['oauth_redirect_uri'] = redirect_uri
            logger.debug(f"Stored redirect URI in session: {redirect_uri}")

        # Attempt OAuth redirect
        try:
            return await oauth.google.authorize_redirect(request, redirect_uri)
        except Exception as oauth_error:
            logger.error(f"OAuth redirect failed: {str(oauth_error)}")
            logger.error(f"OAuth error type: {type(oauth_error)}")
            raise HTTPException(status_code=500,
                                detail=f"OAuth redirect failed: {str(oauth_error)}")

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login route: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request):
    """Handle OAuth callback and create session with JWT"""
    logger.info(f"OAuth callback received - Referer: {request.headers.get('referer')}")
    logger.debug(
        f"Session data: {dict(request.session) if hasattr(request, 'session') else 'No session'}")
    logger.debug(f"Query params: {dict(request.query_params)}")

    try:
        logger.debug("Processing OAuth token...")

        # Check if we have the authorization code
        code = request.query_params.get('code')
        if not code:
            logger.error("No authorization code found in callback")
            raise HTTPException(status_code=400, detail="No authorization code received")

        logger.debug(f"Authorization code received: {code[:10]}...")

        # Get the token manually to avoid session issues
        token = await oauth.google.authorize_access_token(request)
        logger.debug(f"Token received: {token.keys() if isinstance(token, dict) else 'Not a dict'}")

        # Extract access token and get user info manually
        access_token = token.get('access_token')
        if not access_token:
            logger.error("No access token in response")
            raise HTTPException(status_code=400, detail="No access token received")

        logger.debug(f"Access token: {access_token[:10]}...")

        # Get user info manually using the access token
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers=headers
            )
            user_response.raise_for_status()
            user_info = user_response.json()

        logger.info(f"OAuth successful for user: {user_info.get('email')}")

        user_data = {
            "email": user_info["email"],
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }

        # Get frontend URL from request
        frontend_url = get_frontend_url(request)

        logger.debug(f"Creating session and JWT for user: {user_data['email']}")

        # Always create session and JWT
        response = RedirectResponse(frontend_url)
        session_id, jwt_token = create_session(response, user_data)

        logger.info(f"Session created: {session_id[:8]}...")
        logger.info(f"JWT token generated for user: {user_data['email']}")
        logger.debug(f"Redirecting to: {frontend_url}")

        return response

    except OAuthError as e:
        logger.error(f"OAuth error: {str(e)}")
        logger.error(f"OAuth error type: {type(e)}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/me")
async def get_me(request: Request):
    """Get current user information (session-based)"""
    logger.debug(f"/me endpoint called - Headers: {dict(request.headers)}")
    logger.debug(f"/me endpoint called - Cookies: {dict(request.cookies)}")

    session = get_session(request)
    if not session:
        logger.debug("No session found in /me request")
        return {"authenticated": False}

    user_ref = session["user"]
    user_doc = user_ref.get()
    user_data = user_doc.to_dict() if user_doc.exists else None

    if user_data:
        logger.debug(f"Session valid for user: {user_data.get('email')}")
    else:
        logger.warning("User document not found in session")

    return {"authenticated": True, "user": user_data}


@router.get("/me-jwt")
async def get_me_jwt(user: dict = Depends(get_current_user_jwt)):
    """Get current user information (JWT-based, stateless)"""
    logger.debug(f"JWT valid for user: {user.get('email')}")
    return {"authenticated": True, "user": user}


@router.get("/logout")
async def logout(request: Request):
    """Logout and clear session"""
    logger.info("Logout request received")
    
    # Get user email before clearing session for SSE broadcast
    session = get_session(request)
    user_email = None
    if session:
        user_ref = session["user"]
        user_doc = user_ref.get()
        if user_doc.exists:
            user_email = user_doc.to_dict().get("email")
            logger.info(f"Logging out user: {user_email}")
    
    response = JSONResponse({"status": "logged_out"})
    clear_session(request, response)
    
    # Broadcast logout event via SSE
    if user_email:
        logger.debug(f"Broadcasting logout event for: {user_email}")
        await broadcast_logout_event(user_email)
    
    logger.info("Logout completed")
    return response


@router.post("/jwt")
async def create_jwt(request: Request, user: dict = Depends(get_current_user)):
    """Create JWT token"""
    logger.debug(f"Creating JWT for user: {user.get('email')}")
    token = create_jwt_token(user)
    logger.debug(f"JWT created successfully for: {user.get('email')}")
    return {"token": token, "user": user}


@router.post("/refresh")
async def refresh_jwt(user: dict = Depends(get_current_user)):
    """Refresh JWT token using session"""
    logger.debug(f"Refreshing JWT for user: {user.get('email')}")
    token = create_jwt_token(user)
    logger.debug(f"JWT refreshed for: {user.get('email')}")
    return {"token": token, "user": user}


@router.post("/refresh-jwt")
async def refresh_jwt_stateless(user: dict = Depends(get_current_user_jwt)):
    """Refresh JWT token using existing JWT (stateless)"""
    logger.debug(f"Refreshing JWT stateless for user: {user.get('email')}")
    token = create_jwt_token(user)
    logger.debug(f"JWT refreshed stateless for: {user.get('email')}")
    return {"token": token, "user": user}


@router.post("/verify-jwt")
async def verify_jwt(request: Request):
    """Verify JWT token"""
    body = await request.json()
    token = body.get("token")

    if not token:
        logger.error("JWT verification failed: No token provided")
        raise HTTPException(status_code=400, detail="Token required")
    
    payload = verify_jwt_token(token)
    if not payload:
        logger.error("JWT verification failed: Invalid or expired token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    logger.debug(f"JWT verified for user: {payload.get('email')}")
    return {"valid": True, "user": payload}


@router.get("/session")
async def get_session_info(request: Request):
    """Get session information (for debugging)"""
    session = get_session(request)
    if not session:
        logger.debug("No session found in /session request")
        return {}

    user_ref = session["user"]
    user_doc = user_ref.get()
    user_data = user_doc.to_dict() if user_doc.exists else None

    logger.debug(
        f"Session info retrieved for user: {user_data.get('email') if user_data else 'Unknown'}")
    return {
        "createdAt": session.get("createdAt"),
        "expiresAt": session.get("expiresAt"),
        "user": user_data
    }


# ----------------- Router Factory -----------------

def create_auth_router(broadcast_func):
    """Create auth router with injected broadcast function"""
    global broadcast_event_func
    broadcast_event_func = broadcast_func
    return router
