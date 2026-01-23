"""
Authentication module for DataPlunge
Handles user authentication, password hashing, JWT tokens, and session management
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import DictCursor

# Load environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("SESSION_LIFETIME_DAYS", "7"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "dbname='dataplunge' user='user' host='localhost' password='admin'",
)


# -----------------------------------------------------------------------------
# Database connection helper
# -----------------------------------------------------------------------------
def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)


# -----------------------------------------------------------------------------
# Password hashing utilities
# -----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


# -----------------------------------------------------------------------------
# JWT token management
# -----------------------------------------------------------------------------
def generate_session_token(user_id: int) -> str:
    """Generate a JWT session token for a user."""
    expiration = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        'user_id': user_id,
        'exp': expiration,
        'iat': datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def validate_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# -----------------------------------------------------------------------------
# User management functions
# -----------------------------------------------------------------------------
def create_user(email: str, password: Optional[str], full_name: Optional[str] = None, google_oauth_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a new user account."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s;", (email,))
            if cursor.fetchone():
                return None  # User already exists

            # Hash password if provided
            password_hash = hash_password(password) if password else None

            # Insert new user
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, full_name, google_oauth_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, email, full_name, created_at;
                """,
                (email, password_hash, full_name, google_oauth_id, datetime.now(timezone.utc), datetime.now(timezone.utc))
            )
            user = cursor.fetchone()
            conn.commit()

            return {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            }
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user by email."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash, full_name, google_oauth_id, created_at, last_login
                FROM users WHERE email = %s;
                """,
                (email,)
            )
            user = cursor.fetchone()

            if not user:
                return None

            return {
                'id': user['id'],
                'email': user['email'],
                'password_hash': user['password_hash'],
                'full_name': user['full_name'],
                'google_oauth_id': user['google_oauth_id'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'last_login': user['last_login'].isoformat() if user['last_login'] else None
            }
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a user by ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, full_name, google_oauth_id, created_at, last_login
                FROM users WHERE id = %s;
                """,
                (user_id,)
            )
            user = cursor.fetchone()

            if not user:
                return None

            return {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'google_oauth_id': user['google_oauth_id'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'last_login': user['last_login'].isoformat() if user['last_login'] else None
            }
    finally:
        conn.close()


def get_user_by_google_id(google_oauth_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user by Google OAuth ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, full_name, google_oauth_id, created_at, last_login
                FROM users WHERE google_oauth_id = %s;
                """,
                (google_oauth_id,)
            )
            user = cursor.fetchone()

            if not user:
                return None

            return {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'google_oauth_id': user['google_oauth_id'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'last_login': user['last_login'].isoformat() if user['last_login'] else None
            }
    finally:
        conn.close()


def update_last_login(user_id: int) -> None:
    """Update the last login timestamp for a user."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET last_login = %s WHERE id = %s;",
                (datetime.now(timezone.utc), user_id)
            )
            conn.commit()
    finally:
        conn.close()


def create_or_update_user_from_google(google_user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a user from Google OAuth information."""
    google_id = google_user_info.get('sub') or google_user_info.get('id')
    email = google_user_info.get('email')
    name = google_user_info.get('name')

    # Check if user exists by Google ID
    user = get_user_by_google_id(google_id)

    if user:
        # Update last login
        update_last_login(user['id'])
        return user

    # Check if user exists by email
    user = get_user_by_email(email)

    if user:
        # Link Google account to existing user
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET google_oauth_id = %s, updated_at = %s WHERE id = %s;",
                    (google_id, datetime.now(timezone.utc), user['id'])
                )
                conn.commit()
            update_last_login(user['id'])
            user['google_oauth_id'] = google_id
            return user
        finally:
            conn.close()

    # Create new user
    return create_user(email=email, password=None, full_name=name, google_oauth_id=google_id)


# -----------------------------------------------------------------------------
# Authentication decorator
# -----------------------------------------------------------------------------
def login_required(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'No authorization token provided'}), 401

        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid authorization header format'}), 401

        token = parts[1]

        # Validate token
        payload = validate_session_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user from database
        user = get_user_by_id(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401

        # Store user in request context
        g.current_user = user

        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current authenticated user from request context."""
    return getattr(g, 'current_user', None)
