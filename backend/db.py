"""
Database utilities and helpers for DataPlunge.
"""

from datetime import datetime, timezone
from flask import g
import psycopg2
from psycopg2.extras import DictCursor

from config import DATABASE_URL


def get_db():
    """Get a shared DB connection for the current request context."""
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    return g.db


def close_db(_error=None):
    """Close DB connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Initialize database teardown for a Flask app."""
    app.teardown_appcontext(close_db)


# -----------------------------------------------------------------------------
# Google Ads Token Storage
# -----------------------------------------------------------------------------
def store_google_ads_refresh_token(customer_id: str, refresh_token: str, user_id: int) -> None:
    """Insert or update a refresh token for a Google Ads customer and user."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO google_ads_tokens (customer_id, user_id, refresh_token, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customer_id, user_id) DO UPDATE
                SET refresh_token = EXCLUDED.refresh_token, updated_at = EXCLUDED.updated_at;
                """,
                (customer_id, user_id, refresh_token, datetime.now(timezone.utc)),
            )
        conn.commit()


def get_google_ads_refresh_token(customer_id: str, user_id: int) -> str | None:
    """Fetch refresh token for a Google Ads customer and user from DB."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT refresh_token FROM google_ads_tokens WHERE customer_id = %s AND user_id = %s;",
                (customer_id, user_id),
            )
            row = cursor.fetchone()
            return row[0] if row else None


def delete_google_ads_refresh_token(customer_id: str, user_id: int) -> None:
    """Delete refresh token from DB (e.g., when invalid)."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM google_ads_tokens WHERE customer_id = %s AND user_id = %s;",
                (customer_id, user_id)
            )
        conn.commit()


def get_google_ads_customer_id(user_id: int) -> str | None:
    """Get one stored customer_id from DB for a specific user."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT customer_id FROM google_ads_tokens WHERE user_id = %s LIMIT 1;",
                (user_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None


# -----------------------------------------------------------------------------
# OAuth Token Storage (GA4, Meta, etc.)
# -----------------------------------------------------------------------------
def store_oauth_token(
    user_id: int,
    provider: str,
    access_token: str,
    refresh_token: str | None = None,
    token_expiry: datetime | None = None,
    provider_account_id: str | None = None
) -> None:
    """Store or update OAuth token for a provider."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO oauth_tokens (user_id, provider, access_token, refresh_token, token_expiry, provider_account_id, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, provider) DO UPDATE
                SET access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    token_expiry = EXCLUDED.token_expiry,
                    provider_account_id = EXCLUDED.provider_account_id,
                    updated_at = EXCLUDED.updated_at;
                """,
                (user_id, provider, access_token, refresh_token, token_expiry, provider_account_id, datetime.now(timezone.utc))
            )
        conn.commit()


def get_oauth_token(user_id: int, provider: str) -> dict | None:
    """Get OAuth token for a provider."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT access_token, refresh_token, token_expiry, provider_account_id
                FROM oauth_tokens
                WHERE user_id = %s AND provider = %s;
                """,
                (user_id, provider)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'access_token': row[0],
                'refresh_token': row[1],
                'token_expiry': row[2],
                'provider_account_id': row[3]
            }


def delete_oauth_token(user_id: int, provider: str) -> None:
    """Delete OAuth token for a provider."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM oauth_tokens WHERE user_id = %s AND provider = %s;",
                (user_id, provider)
            )
        conn.commit()


# -----------------------------------------------------------------------------
# Datasource Helpers
# -----------------------------------------------------------------------------
def get_or_create_datasource(user_id: int, source_name: str) -> int:
    """Get or create a datasource for a user, returns the datasource ID."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM datasources WHERE source_name = %s AND user_id = %s LIMIT 1;",
                (source_name, user_id),
            )
            ds_row = cursor.fetchone()

            if ds_row:
                return ds_row[0]

            cursor.execute(
                "INSERT INTO datasources (user_id, source_name) VALUES (%s, %s) RETURNING id;",
                (user_id, source_name),
            )
            data_source_id = cursor.fetchone()[0]
            conn.commit()
            return data_source_id


def get_datasource_id(user_id: int, source_name: str) -> int | None:
    """Get datasource ID for a user and source name."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM datasources WHERE source_name = %s AND user_id = %s LIMIT 1;",
                (source_name, user_id),
            )
            row = cursor.fetchone()
            return row[0] if row else None


# -----------------------------------------------------------------------------
# Campaign Helpers
# -----------------------------------------------------------------------------
def get_or_create_campaign(
    campaign_name: str,
    data_source_id: int | None = None,
    external_id: str | None = None,
    campaign_id: int | None = None
) -> int:
    """
    Get or create a campaign, returns the campaign ID.

    If campaign_id is provided, uses that as the ID (for Google Ads).
    If external_id is provided, looks up by (data_source_id, external_id) first.
    Otherwise, looks up by campaign_name.
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            # If we have an external_id and data_source_id, look up by those
            if external_id and data_source_id:
                cursor.execute(
                    "SELECT id FROM campaigns WHERE data_source_id = %s AND external_id = %s LIMIT 1;",
                    (data_source_id, external_id),
                )
                existing = cursor.fetchone()
                if existing:
                    return existing[0]

                # Insert with external_id
                cursor.execute(
                    "INSERT INTO campaigns (campaign_name, data_source_id, external_id) VALUES (%s, %s, %s) RETURNING id;",
                    (campaign_name, data_source_id, external_id),
                )
                new_id = cursor.fetchone()[0]
                conn.commit()
                return new_id

            # If campaign_id is provided (Google Ads style), use it directly
            if campaign_id:
                cursor.execute("SELECT id FROM campaigns WHERE id = %s LIMIT 1;", (campaign_id,))
                existing = cursor.fetchone()
                if existing:
                    return existing[0]

                cursor.execute(
                    "INSERT INTO campaigns (id, campaign_name) VALUES (%s, %s) RETURNING id;",
                    (campaign_id, campaign_name),
                )
                new_id = cursor.fetchone()[0]
                conn.commit()
                return new_id

            # Fallback: look up by name only
            cursor.execute(
                "SELECT id FROM campaigns WHERE campaign_name = %s LIMIT 1;",
                (campaign_name,),
            )
            existing = cursor.fetchone()
            if existing:
                return existing[0]

            cursor.execute(
                "INSERT INTO campaigns (campaign_name) VALUES (%s) RETURNING id;",
                (campaign_name,),
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id


def upsert_performance_metrics(
    data_source_id: int,
    campaign_id: int,
    date: str,
    costs: float = 0,
    impressions: int = 0,
    clicks: int = 0,
    cost_per_click: float = 0,
    sessions: int = 0,
    conversions: int = 0,
    cost_per_conversion: float = 0
) -> None:
    """Insert or update performance metrics for a campaign on a date."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO performanceMetrics (
                    data_source_id, campaign_id, date, costs, impressions, clicks,
                    cost_per_click, sessions, conversions, cost_per_conversion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (data_source_id, campaign_id, date) DO UPDATE
                SET costs = EXCLUDED.costs,
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    cost_per_click = EXCLUDED.cost_per_click,
                    sessions = EXCLUDED.sessions,
                    conversions = EXCLUDED.conversions,
                    cost_per_conversion = EXCLUDED.cost_per_conversion;
                """,
                (
                    data_source_id,
                    campaign_id,
                    date,
                    costs,
                    impressions,
                    clicks,
                    cost_per_click,
                    sessions,
                    conversions,
                    cost_per_conversion,
                ),
            )
        conn.commit()
