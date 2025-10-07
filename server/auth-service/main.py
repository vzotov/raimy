import asyncio
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

# Import auth router
from auth import router as auth_router, oauth


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Auth Microservice...")
    yield
    print("Shutting down Auth Microservice...")


app = FastAPI(
    title="Raimy Auth Service",
    description="""
    ## 🔐 Raimy Authentication Microservice

    Dedicated authentication service handling OAuth, JWT tokens, and session management.

    ### Features:
    * 🔐 **Google OAuth** - OAuth 2.0 authentication flow
    * 🎫 **JWT Tokens** - Stateless token generation and verification
    * 📝 **Session Management** - Firestore-backed sessions
    * 🔄 **Token Refresh** - Automatic token renewal

    ### Endpoints:
    - `POST /auth/login` - Initiate Google OAuth
    - `GET /auth/callback` - Handle OAuth callback
    - `POST /auth/verify` - Verify JWT/session
    - `POST /auth/refresh` - Refresh tokens
    - `POST /auth/logout` - Terminate session
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add SessionMiddleware for OAuth support
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SIGNER_SECRET", "supersecret")
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Google OAuth client
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if os.getenv("AUTH_DEBUG", "false").lower() == "true":
    logger.setLevel(logging.DEBUG)

google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

if not google_client_id or not google_client_secret:
    logger.warning("Google OAuth credentials not found!")
    logger.warning("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables")
else:
    try:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            access_token_url="https://accounts.google.com/o/oauth2/token",
            access_token_params=None,
            authorize_url="https://accounts.google.com/o/oauth2/auth",
            authorize_params=None,
            api_base_url="https://www.googleapis.com/oauth2/v1/",
            jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
            client_kwargs={
                "scope": "openid email profile",
                "token_endpoint_auth_method": "client_secret_post"
            },
            # Disable state validation to avoid session issues
            authorize_state=None,
        )
        logger.info("Google OAuth client registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Google OAuth client: {e}")


@app.get("/", tags=["Root"])
async def root():
    """Auth Service Root"""
    return {
        "service": "Raimy Auth Microservice",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth/*",
            "health": "/health"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health Check"""
    return {
        "service": "auth-service",
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }


# Include auth router
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")