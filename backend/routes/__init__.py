"""
Routes package for DataPlunge backend.
"""

from flask import Blueprint

# Import all route blueprints
from .auth import auth_bp
from .datasources import datasources_bp
from .google_ads import google_ads_bp
from .google_analytics import google_analytics_bp
from .meta import meta_bp
from .reporting import reporting_bp


def register_routes(app):
    """Register all route blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(datasources_bp)
    app.register_blueprint(google_ads_bp)
    app.register_blueprint(google_analytics_bp)
    app.register_blueprint(meta_bp)
    app.register_blueprint(reporting_bp)
