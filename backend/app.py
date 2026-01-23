"""
DataPlunge Backend - Main Application Entry Point

A multi-channel marketing analytics platform that aggregates campaign performance
data from Google Ads, Google Analytics (GA4), and Meta (Facebook) Ads.
"""

from flask import Flask
from flask_cors import CORS
from flask_session import Session

from config import FLASK_SECRET_KEY, CORS_ORIGINS
from db import init_db
from routes import register_routes


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    # Session configuration
    app.config.update(
        SESSION_TYPE="filesystem",
        SESSION_COOKIE_NAME="dataplunge-session",
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,  # Set True behind HTTPS in production
        SESSION_COOKIE_DOMAIN="localhost",  # Adjust for production domain
    )
    Session(app)

    # CORS configuration
    CORS(app, supports_credentials=True, origins=CORS_ORIGINS)

    # Initialize database teardown
    init_db(app)

    # Register all route blueprints
    register_routes(app)

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
