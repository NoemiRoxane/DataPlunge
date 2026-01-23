"""
Authentication routes for DataPlunge.
Handles user registration, login, logout, and Google OAuth for user authentication.
"""

import requests
from flask import Blueprint, jsonify, redirect, request, session
from email_validator import validate_email, EmailNotValidError
from google_auth_oauthlib.flow import Flow

from auth import (
    login_required,
    get_current_user,
    create_user,
    get_user_by_email,
    verify_password,
    generate_session_token,
    create_or_update_user_from_google,
    update_last_login,
)
from config import (
    FRONTEND_BASE_URL,
    GOOGLE_USER_AUTH_CLIENT_ID,
    GOOGLE_USER_AUTH_CLIENT_SECRET,
    GOOGLE_USER_AUTH_REDIRECT_URI,
    get_google_oauth_client_config,
)
from constants import GOOGLE_USER_AUTH_SCOPES

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account with email/password."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Validate email
    try:
        validate_email(email)
    except EmailNotValidError as e:
        return jsonify({"error": f"Invalid email: {str(e)}"}), 400

    # Validate password strength
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    # Create user
    user = create_user(email, password, full_name)

    if not user:
        return jsonify({"error": "User with this email already exists"}), 400

    # Generate session token
    token = generate_session_token(user['id'])

    # Update last login
    update_last_login(user['id'])

    return jsonify({
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name']
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login with email and password."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Get user by email
    user = get_user_by_email(email)

    if not user or not user.get('password_hash'):
        return jsonify({"error": "Invalid email or password"}), 401

    # Verify password
    if not verify_password(password, user['password_hash']):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate session token
    token = generate_session_token(user['id'])

    # Update last login
    update_last_login(user['id'])

    return jsonify({
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name']
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    """Get current user information."""
    user = get_current_user()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user['id'],
        "email": user['email'],
        "full_name": user['full_name'],
        "created_at": user.get('created_at'),
        "last_login": user.get('last_login')
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout current user."""
    # For JWT-based auth, logout is handled client-side by removing the token
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/google/login")
def google_user_auth_login():
    """Initiate Google OAuth for user authentication."""
    client_config = get_google_oauth_client_config(
        GOOGLE_USER_AUTH_CLIENT_ID,
        GOOGLE_USER_AUTH_CLIENT_SECRET,
        GOOGLE_USER_AUTH_REDIRECT_URI,
    )

    flow = Flow.from_client_config(client_config, scopes=GOOGLE_USER_AUTH_SCOPES)
    flow.redirect_uri = GOOGLE_USER_AUTH_REDIRECT_URI

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    session["google_user_auth_state"] = state
    return redirect(auth_url)


@auth_bp.route("/google/callback")
def google_user_auth_callback():
    """Handle Google OAuth callback for user authentication."""
    client_config = get_google_oauth_client_config(
        GOOGLE_USER_AUTH_CLIENT_ID,
        GOOGLE_USER_AUTH_CLIENT_SECRET,
        GOOGLE_USER_AUTH_REDIRECT_URI,
    )

    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_USER_AUTH_SCOPES,
        state=session.get("google_user_auth_state"),
    )
    flow.redirect_uri = GOOGLE_USER_AUTH_REDIRECT_URI

    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch token: {str(e)}"}), 400

    creds = flow.credentials

    # Get user info from Google
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(userinfo_url, headers=headers, timeout=30)

    if not response.ok:
        return jsonify({"error": "Failed to get user info from Google"}), 400

    google_user_info = response.json()

    # Create or update user
    user = create_or_update_user_from_google(google_user_info)

    if not user:
        return jsonify({"error": "Failed to create user"}), 500

    # Generate session token
    token = generate_session_token(user['id'])

    # Redirect to frontend with token
    redirect_url = f"{FRONTEND_BASE_URL}/auth/callback?token={token}"
    return redirect(redirect_url)
