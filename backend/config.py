"""
Configuration management for DataPlunge backend.
Loads and validates environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def require_env(name: str) -> str:
    """Get a required environment variable or raise an error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_env(name: str, default: str = "") -> str:
    """Get an optional environment variable with a default."""
    return os.getenv(name, default)


# -----------------------------------------------------------------------------
# Flask Configuration
# -----------------------------------------------------------------------------
FLASK_SECRET_KEY = require_env("FLASK_SECRET_KEY")
FLASK_DEBUG = get_env("FLASK_DEBUG", "True").lower() == "true"

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
DATABASE_URL = get_env(
    "DATABASE_URL",
    "dbname='dataplunge' user='user' host='localhost' password='admin'",
)

# -----------------------------------------------------------------------------
# Frontend / CORS Configuration
# -----------------------------------------------------------------------------
FRONTEND_BASE_URL = get_env("FRONTEND_BASE_URL", "http://localhost:3000")
CORS_ORIGINS = get_env("CORS_ORIGINS", FRONTEND_BASE_URL).split(",")

# -----------------------------------------------------------------------------
# Google Ads Configuration
# -----------------------------------------------------------------------------
GOOGLE_ADS_CLIENT_ID = require_env("GOOGLE_ADS_CLIENT_ID")
GOOGLE_ADS_CLIENT_SECRET = require_env("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_REDIRECT_URI = require_env("GOOGLE_ADS_REDIRECT_URI")
GOOGLE_ADS_DEVELOPER_TOKEN = require_env("GOOGLE_ADS_DEVELOPER_TOKEN")

# -----------------------------------------------------------------------------
# Google Analytics (GA4) Configuration
# -----------------------------------------------------------------------------
GA_CLIENT_ID = require_env("GA_CLIENT_ID")
GA_CLIENT_SECRET = require_env("GA_CLIENT_SECRET")
GA_REDIRECT_URI = require_env("GA_REDIRECT_URI")

# -----------------------------------------------------------------------------
# Meta (Facebook) Configuration
# -----------------------------------------------------------------------------
META_APP_ID = require_env("META_APP_ID")
META_APP_SECRET = require_env("META_APP_SECRET")
META_REDIRECT_URI = require_env("META_REDIRECT_URI")

# -----------------------------------------------------------------------------
# Google OAuth for User Authentication
# -----------------------------------------------------------------------------
GOOGLE_USER_AUTH_CLIENT_ID = require_env("GOOGLE_USER_AUTH_CLIENT_ID")
GOOGLE_USER_AUTH_CLIENT_SECRET = require_env("GOOGLE_USER_AUTH_CLIENT_SECRET")
GOOGLE_USER_AUTH_REDIRECT_URI = require_env("GOOGLE_USER_AUTH_REDIRECT_URI")

# -----------------------------------------------------------------------------
# OAuth Development Setting
# -----------------------------------------------------------------------------
# Allow OAuth over HTTP for local development (do NOT use in production)
OAUTHLIB_INSECURE_TRANSPORT = get_env("OAUTHLIB_INSECURE_TRANSPORT", "1")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = OAUTHLIB_INSECURE_TRANSPORT


def get_google_oauth_client_config(client_id: str, client_secret: str, redirect_uri: str) -> dict:
    """Generate Google OAuth client configuration dictionary."""
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
