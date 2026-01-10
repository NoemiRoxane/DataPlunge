import os
from datetime import datetime, timedelta

import psycopg2
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, session, g
from flask_cors import CORS
from flask_session import Session
from psycopg2.extras import DictCursor

from google.ads.googleads.client import GoogleAdsClient
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials as GoogleCredentials

from google_auth_oauthlib.flow import Flow
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
)
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import ListPropertiesRequest
from google.auth.transport.requests import Request as GARequest
from google.oauth2.credentials import Credentials as GACredentials

# -----------------------------------------------------------------------------
# Local development setting: allow OAuth over HTTP (do NOT use in production).
# -----------------------------------------------------------------------------
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "1")

# -----------------------------------------------------------------------------
# Load environment + configuration
# -----------------------------------------------------------------------------
load_dotenv()


def require_env(name: str, value: str | None) -> str:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


FLASK_SECRET_KEY = require_env("FLASK_SECRET_KEY", os.getenv("FLASK_SECRET_KEY"))

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", FRONTEND_BASE_URL).split(",")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "dbname='dataplunge' user='user' host='localhost' password='admin'",
)

# Google Ads
GOOGLE_ADS_CLIENT_ID = require_env("GOOGLE_ADS_CLIENT_ID", os.getenv("GOOGLE_ADS_CLIENT_ID"))
GOOGLE_ADS_CLIENT_SECRET = require_env("GOOGLE_ADS_CLIENT_SECRET", os.getenv("GOOGLE_ADS_CLIENT_SECRET"))
GOOGLE_ADS_REDIRECT_URI = require_env("GOOGLE_ADS_REDIRECT_URI", os.getenv("GOOGLE_ADS_REDIRECT_URI"))
GOOGLE_ADS_DEVELOPER_TOKEN = require_env("GOOGLE_ADS_DEVELOPER_TOKEN", os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"))

# Google Analytics (GA4)
GA_CLIENT_ID = require_env("GA_CLIENT_ID", os.getenv("GA_CLIENT_ID"))
GA_CLIENT_SECRET = require_env("GA_CLIENT_SECRET", os.getenv("GA_CLIENT_SECRET"))
GA_REDIRECT_URI = require_env("GA_REDIRECT_URI", os.getenv("GA_REDIRECT_URI"))

# Meta
META_APP_ID = require_env("META_APP_ID", os.getenv("META_APP_ID"))
META_APP_SECRET = require_env("META_APP_SECRET", os.getenv("META_APP_SECRET"))
META_REDIRECT_URI = require_env("META_REDIRECT_URI", os.getenv("META_REDIRECT_URI"))


# -----------------------------------------------------------------------------
# Flask app setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

app.config.update(
    SESSION_TYPE="filesystem",
    SESSION_COOKIE_NAME="dataplunge-session",
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # set True behind HTTPS
    SESSION_COOKIE_DOMAIN="localhost",  # adjust for prod domain
)
Session(app)

CORS(app, supports_credentials=True, origins=CORS_ORIGINS)


# -----------------------------------------------------------------------------
# Database helpers
# -----------------------------------------------------------------------------
def get_db():
    """Get a shared DB connection for the current request context."""
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    return g.db


@app.teardown_appcontext
def close_db(_error):
    """Close DB connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# -----------------------------------------------------------------------------
# Google Ads token storage (DB)
# -----------------------------------------------------------------------------
def store_refresh_token(customer_id: str, refresh_token: str) -> None:
    """Insert or update a refresh token for a customer."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO google_ads_tokens (customer_id, refresh_token)
                VALUES (%s, %s)
                ON CONFLICT (customer_id) DO UPDATE
                SET refresh_token = EXCLUDED.refresh_token;
                """,
                (customer_id, refresh_token),
            )
        conn.commit()


def get_refresh_token(customer_id: str) -> str | None:
    """Fetch refresh token for a customer from DB."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT refresh_token FROM google_ads_tokens WHERE customer_id = %s;",
                (customer_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None


def delete_refresh_token(customer_id: str) -> None:
    """Delete refresh token from DB (e.g., when invalid)."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM google_ads_tokens WHERE customer_id = %s;", (customer_id,))
        conn.commit()


def refresh_access_token(customer_id: str) -> str | None:
    """Refresh a Google OAuth access token using stored refresh token (DB)."""
    refresh_token = get_refresh_token(customer_id)
    if not refresh_token:
        print(f"❌ No refresh token found for customer {customer_id}. Re-authentication required.")
        return None

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_ADS_CLIENT_ID,
        "client_secret": GOOGLE_ADS_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(token_url, data=token_data, timeout=30)
    token_json = response.json()

    if "access_token" in token_json:
        session["access_token"] = token_json["access_token"]
        return token_json["access_token"]

    # If refresh token is invalid, remove it so the user must re-auth.
    if token_json.get("error") == "invalid_grant":
        print(f"🔄 Refresh token invalid for customer {customer_id}. Removing from DB.")
        delete_refresh_token(customer_id)

    print(f"❌ Failed to refresh access token: {token_json}")
    return None


def get_customer_ids_from_api(access_token: str) -> list[str]:
    url = "https://googleads.googleapis.com/v22/customers:listAccessibleCustomers"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": GOOGLE_ADS_DEVELOPER_TOKEN,  # <-- important
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=30)

    # If not 2xx, print useful diagnostics
    if not response.ok:
        content_type = response.headers.get("Content-Type", "")
        print("Google Ads API ERROR")
        print("Status:", response.status_code)
        print("Content-Type:", content_type)
        print("Body:", response.text[:2000])  # limit
        response.raise_for_status()

    # Even if 2xx, still ensure it's JSON
    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type.lower():
        print("Unexpected non-JSON response")
        print("Status:", response.status_code)
        print("Content-Type:", content_type)
        print("Body:", response.text[:2000])
        raise ValueError("Expected JSON but got non-JSON response from Google Ads API")

    data = response.json()

    # Parse resource names like: "customers/1234567890"
    resource_names = data.get("resourceNames", [])
    customer_ids = [rn.split("/")[1] for rn in resource_names if rn.startswith("customers/")]

    return customer_ids

def get_customer_id_from_db() -> str | None:
    """Get one stored customer_id from DB (simple fallback)."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT customer_id FROM google_ads_tokens LIMIT 1;")
            row = cursor.fetchone()
            return row[0] if row else None


def get_google_ads_client(customer_id: str) -> GoogleAdsClient | None:
    """Create GoogleAdsClient using refresh token from DB."""
    refresh_token = get_refresh_token(customer_id)
    if not refresh_token:
        print(f"❌ No refresh token found for customer {customer_id}.")
        return None

    # Optional: verify token can be refreshed (helps early detection).
    try:
        creds = GoogleCredentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_ADS_CLIENT_ID,
            client_secret=GOOGLE_ADS_CLIENT_SECRET,
        )
        creds.refresh(GoogleRequest())
    except Exception as e:
        print(f"❌ Google OAuth refresh failed for customer {customer_id}: {e}")
        return None

    try:
        return GoogleAdsClient.load_from_dict(
            {
                "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
                "use_proto_plus": True,
                # NOTE: login_customer_id is normally the manager account ID.
                # You used customer_id previously; keep for compatibility.
                "login_customer_id": customer_id,
                "client_id": GOOGLE_ADS_CLIENT_ID,
                "client_secret": GOOGLE_ADS_CLIENT_SECRET,
                "refresh_token": refresh_token,
            }
        )
    except Exception as e:
        print(f"❌ Failed to build GoogleAdsClient for {customer_id}: {e}")
        return None


# -----------------------------------------------------------------------------
# Google Ads OAuth routes
# -----------------------------------------------------------------------------
@app.route("/google-ads/login")
def google_ads_login():
    """Step 1: Redirect user to Google OAuth consent screen."""
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_ADS_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_ADS_REDIRECT_URI}"
        "&response_type=code"
        "&scope=https://www.googleapis.com/auth/adwords"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(auth_url)


@app.route("/google-ads/callback")
def google_ads_callback():
    """Step 2: Handle Google OAuth callback and store refresh token(s)."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization failed"}), 400

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_ADS_CLIENT_ID,
        "client_secret": GOOGLE_ADS_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_ADS_REDIRECT_URI,
    }

    response = requests.post(token_url, data=token_data, timeout=30)

    if not response.ok:
        return jsonify({
            "error": "Token exchange failed (HTTP)",
            "status": response.status_code,
            "body": response.text[:2000],
        }), 400

    try:
        token_json = response.json()
    except ValueError:
        return jsonify({
            "error": "Token exchange failed (non-JSON response)",
            "status": response.status_code,
            "body": response.text[:2000],
            "content_type": response.headers.get("Content-Type"),
        }), 400

    if "access_token" not in token_json:
        return jsonify({"error": "Token exchange failed", "details": token_json}), 400

    access_token = token_json["access_token"]
    refresh_token = token_json.get("refresh_token")

    customer_ids = get_customer_ids_from_api(access_token)
    if not customer_ids:
        return jsonify({"error": "Failed to fetch customer IDs"}), 500

    # Store refresh token per customer (if Google returns one).
    for cid in customer_ids:
        if refresh_token:
            store_refresh_token(cid, refresh_token)
            print(f"✅ Stored refresh token for customer {cid}.")
        else:
            print(f"⚠️ No refresh token returned for customer {cid} (already granted before?).")

    # Optional: store one customer_id in session as a default
    session["customer_id"] = customer_ids[0]

    # Trigger initial fetch (same behavior as before)
    fetch_and_store_campaigns()

    # Redirect user back to main page (React)
    return redirect(FRONTEND_BASE_URL)



@app.route("/google-ads/fetch-campaigns")
def fetch_and_store_campaigns():
    """Fetch Google Ads campaign performance and store it in DB."""
    customer_id = session.get("customer_id") or get_customer_id_from_db()
    if not customer_id:
        return jsonify({"error": "Customer ID not found"}), 400

    client = get_google_ads_client(customer_id)
    if not client:
        return jsonify({"error": "Could not create Google Ads client"}), 500

    try:
        ga_service = client.get_service("GoogleAdsService")
    except Exception as e:
        return jsonify({"error": "Google Ads client error", "details": str(e)}), 500

    query = """
        SELECT
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.average_cpc,
            metrics.interactions,
            metrics.conversions,
            metrics.cost_per_conversion,
            segments.date
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY campaign.id, segments.date
    """

    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)
    except Exception as e:
        return jsonify({"error": "Google Ads API request failed", "details": str(e)}), 500

    campaign_rows: list[dict] = []
    for batch in response:
        for row in batch.results:
            metrics = row.metrics
            campaign_rows.append(
                {
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                    "date": row.segments.date,
                    "costs": metrics.cost_micros / 1e6,
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "cost_per_click": (metrics.average_cpc / 1e6) if metrics.average_cpc else 0,
                    "sessions": metrics.interactions or 0,
                    "conversions": metrics.conversions or 0,
                    "cost_per_conversion": (metrics.cost_per_conversion / 1e6) if metrics.cost_per_conversion else 0,
                }
            )

    if not campaign_rows:
        return jsonify({"error": "No campaigns found"}), 404

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM datasources WHERE source_name = 'Google Ads' LIMIT 1;")
            ds_row = cursor.fetchone()
            if not ds_row:
                return jsonify({"error": "No data_source_id found for 'Google Ads'"}), 500
            data_source_id = ds_row[0]

            for row in campaign_rows:
                cursor.execute("SELECT id FROM campaigns WHERE id = %s LIMIT 1;", (row["campaign_id"],))
                existing = cursor.fetchone()

                if not existing:
                    cursor.execute(
                        "INSERT INTO campaigns (id, campaign_name) VALUES (%s, %s) RETURNING id;",
                        (row["campaign_id"], row["campaign_name"]),
                    )
                    campaign_id = cursor.fetchone()[0]
                else:
                    campaign_id = existing[0]

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
                        row["date"],
                        row["costs"],
                        row["impressions"],
                        row["clicks"],
                        row["cost_per_click"],
                        row["sessions"],
                        row["conversions"],
                        row["cost_per_conversion"],
                    ),
                )

        conn.commit()

    return jsonify({"message": "Campaign data stored successfully"}), 200


# -----------------------------------------------------------------------------
# Google Analytics (GA4) helpers + routes
# -----------------------------------------------------------------------------
def get_ga_client() -> BetaAnalyticsDataClient | None:
    """Build a GA4 client from OAuth token stored in session."""
    creds_data = session.get("ga_token")
    if not creds_data:
        return None

    creds = GACredentials(
        token=creds_data["token"],
        refresh_token=creds_data.get("refresh_token"),
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"],
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(GARequest())

    return BetaAnalyticsDataClient(credentials=creds)

@app.route("/ga/login")
def ga_login():
    ga_scopes = [
        "https://www.googleapis.com/auth/analytics.readonly",
        "https://www.googleapis.com/auth/analytics.edit",
        "https://www.googleapis.com/auth/analytics.manage.users",
        "https://www.googleapis.com/auth/analytics",
        "https://www.googleapis.com/auth/adwords",
    ]

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GA_CLIENT_ID,
                "client_secret": GA_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GA_REDIRECT_URI],
            }
        },
        scopes=ga_scopes,
    )
    flow.redirect_uri = GA_REDIRECT_URI

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    session["ga_state"] = state   # ✅ STORE STATE
    return redirect(auth_url)

@app.route("/ga/callback")
def ga_callback():
    ga_scopes = [
        "https://www.googleapis.com/auth/analytics.readonly",
        "https://www.googleapis.com/auth/analytics.edit",
        "https://www.googleapis.com/auth/analytics.manage.users",
        "https://www.googleapis.com/auth/analytics",
        "https://www.googleapis.com/auth/adwords",
    ]

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GA_CLIENT_ID,
                "client_secret": GA_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GA_REDIRECT_URI],
            }
        },
        scopes=ga_scopes,
        state=session.get("ga_state"),   # ✅ REUSE STATE
    )
    flow.redirect_uri = GA_REDIRECT_URI

    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials

    session["ga_token"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }

    return redirect(f"{FRONTEND_BASE_URL}/connect/google-analytics?ga_ready=true")

@app.route("/ga/properties")
def get_ga_properties():
    creds_data = session.get("ga_token")
    if not creds_data:
        return jsonify({"error": "Not authenticated"}), 401

    creds = GACredentials(
        token=creds_data["token"],
        refresh_token=creds_data.get("refresh_token"),
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"],
    )
    creds.refresh(GARequest())

    admin_client = AnalyticsAdminServiceClient(credentials=creds)

    properties: list[dict] = []
    try:
        accounts = admin_client.list_accounts()
    except Exception as e:
        return jsonify({"error": f"Failed to load GA accounts: {e}"}), 500

    for account in accounts:
        account_id = account.name.split("/")[-1]
        try:
            req = ListPropertiesRequest(filter=f"parent:accounts/{account_id}")
            props = admin_client.list_properties(request=req)
            for prop in props:
                properties.append(
                    {
                        "property_id": prop.name.split("/")[-1],
                        "display_name": prop.display_name,
                        "time_zone": prop.time_zone,
                    }
                )
        except Exception as e:
            print(f"⚠️ Failed to load properties for {account.name}: {e}")

    return jsonify(properties)


@app.route("/ga/fetch-metrics")
def fetch_ga_data():
    client = get_ga_client()
    if not client:
        return jsonify({"error": "Not authenticated with GA4"}), 401

    property_id = request.args.get("property_id")
    if not property_id:
        return jsonify({"error": "property_id is required"}), 400

    req = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[{"name": "date"}],
        metrics=[{"name": "sessions"}, {"name": "totalUsers"}, {"name": "bounceRate"}],
        date_ranges=[{"start_date": "30daysAgo", "end_date": "today"}],
    )

    response = client.run_report(request=req)
    rows = []
    for row in response.rows:
        rows.append(
            {
                "date": row.dimension_values[0].value,
                "sessions": row.metric_values[0].value,
                "users": row.metric_values[1].value,
                "bounce_rate": row.metric_values[2].value,
            }
        )
    return jsonify(rows)


@app.route("/ga/fetch-campaigns")
def fetch_ga_campaigns():
    client = get_ga_client()
    if not client:
        return jsonify({"error": "Not authenticated with GA4"}), 401

    property_id = request.args.get("property_id")
    if not property_id:
        return jsonify({"error": "property_id is required"}), 400
    
    user_id = session.get("user_id")

    if not user_id:
        user_id = 1
        session["user_id"] = user_id

    req = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date"), Dimension(name="sessionCampaignName")],
        metrics=[Metric(name="sessions"), Metric(name="totalUsers"), Metric(name="bounceRate")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    )

    try:
        response = client.run_report(request=req)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch GA data: {e}"}), 500

    with get_db() as conn:
        with conn.cursor() as cursor:

            # ✅ Google Analytics datasource pro user
            cursor.execute(
                "SELECT id FROM datasources WHERE source_name = %s AND user_id = %s LIMIT 1;",
                ("Google Analytics", user_id),
            )
            ds_row = cursor.fetchone()

            if not ds_row:
                cursor.execute(
                    "INSERT INTO datasources (user_id, source_name) VALUES (%s, %s) RETURNING id;",
                    (user_id, "Google Analytics"),
                )
                data_source_id = cursor.fetchone()[0]
            else:
                data_source_id = ds_row[0]

            for row in response.rows:
                campaign_name = row.dimension_values[1].value or "(not set)"
                raw_date = row.dimension_values[0].value  # YYYYMMDD
                formatted_date = datetime.strptime(raw_date, "%Y%m%d").date()
                sessions_val = int(row.metric_values[0].value or 0)

                # ✅ Campaigns (erstmal wie bei dir - falls campaigns.user_id NOT NULL ist, sag Bescheid)
                cursor.execute(
                    "SELECT id FROM campaigns WHERE campaign_name = %s LIMIT 1;",
                    (campaign_name,),
                )
                existing = cursor.fetchone()

                if existing:
                    campaign_id = existing[0]
                else:
                    cursor.execute(
                        "INSERT INTO campaigns (campaign_name) VALUES (%s) RETURNING id;",
                        (campaign_name,),
                    )
                    campaign_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO performanceMetrics (
                        data_source_id, campaign_id, date,
                        costs, impressions, clicks, cost_per_click,
                        sessions, conversions, cost_per_conversion
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (data_source_id, campaign_id, date) DO UPDATE
                    SET
                        sessions = EXCLUDED.sessions,
                        costs = EXCLUDED.costs,
                        impressions = EXCLUDED.impressions,
                        clicks = EXCLUDED.clicks,
                        cost_per_click = EXCLUDED.cost_per_click,
                        conversions = EXCLUDED.conversions,
                        cost_per_conversion = EXCLUDED.cost_per_conversion;
                    """,
                    (
                        data_source_id,
                        campaign_id,
                        formatted_date,
                        0,  # costs
                        0,  # impressions
                        0,  # clicks
                        0,  # cost_per_click
                        sessions_val,
                        0,  # conversions
                        0,  # cost_per_conversion
                    ),
                )

        conn.commit()
    return jsonify({"message": "Google Analytics campaign data stored"}), 200


# -----------------------------------------------------------------------------
# Meta routes
# -----------------------------------------------------------------------------
@app.route("/meta/login")
def meta_login():
    oauth_url = (
        "https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        "&scope=ads_read,ads_management"
        "&response_type=code"
        "&state=xyz"
    )
    return redirect(oauth_url)


@app.route("/meta/callback")
def meta_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "redirect_uri": META_REDIRECT_URI,
        "code": code,
    }

    res = requests.get(token_url, params=params, timeout=30)
    token_info = res.json()

    if "access_token" not in token_info:
        return jsonify({"error": "Failed to fetch token", "details": token_info}), 400

    session["meta_token"] = token_info["access_token"]
    return redirect(f"{FRONTEND_BASE_URL}/connect/meta?meta_ready=true")


@app.route("/meta/adaccounts")
def meta_adaccounts():
    access_token = session.get("meta_token")
    if not access_token:
        return jsonify({"error": "Not logged in"}), 401

    res = requests.get(
        "https://graph.facebook.com/v19.0/me/adaccounts",
        params={"access_token": access_token, "fields": "id,name,account_status"},
        timeout=30,
    )

    data = res.json()
    if "data" not in data:
        return jsonify({"error": "Could not load ad accounts", "details": data}), 500

    return jsonify(data["data"])


@app.route("/meta/select-account", methods=["POST"])
def select_meta_account():
    payload = request.get_json(silent=True) or {}
    account_id = payload.get("account_id")

    if not account_id:
        return jsonify({"error": "account_id is required"}), 400

    session["meta_account_id"] = account_id

    # Optional: trigger fetch immediately, same as your original behavior
    return fetch_and_store_meta_campaigns()


@app.route("/meta/fetch-campaigns")
def fetch_and_store_meta_campaigns():
    access_token = session.get("meta_token")
    account_id = session.get("meta_account_id")

    if not access_token:
        return jsonify({"error": "Not logged in"}), 401
    if not account_id:
        return jsonify({"error": "No Meta ad account selected"}), 400

    # Fetch campaigns
    url = f"https://graph.facebook.com/v19.0/{account_id}/campaigns"
    params = {
        "fields": "id,name,status",
        "effective_status": '["ACTIVE","PAUSED"]',
        "access_token": access_token,
    }
    res = requests.get(url, params=params, timeout=30)
    campaigns_json = res.json()

    if "data" not in campaigns_json or not campaigns_json["data"]:
        return jsonify({"error": "No campaigns found", "details": campaigns_json}), 404

    campaigns = campaigns_json["data"]

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM datasources WHERE source_name = 'Meta' LIMIT 1;")
            ds_row = cursor.fetchone()
            if not ds_row:
                return jsonify({"error": "Meta not found in datasources"}), 500
            data_source_id = ds_row[0]

            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=30)

            inserted = 0

            for campaign in campaigns:
                campaign_id = int(campaign["id"])
                campaign_name = campaign["name"]

                cursor.execute("SELECT id FROM campaigns WHERE id = %s LIMIT 1;", (campaign_id,))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute(
                        "INSERT INTO campaigns (id, campaign_name) VALUES (%s, %s) RETURNING id;",
                        (campaign_id, campaign_name),
                    )
                    campaign_db_id = cursor.fetchone()[0]
                else:
                    campaign_db_id = existing[0]

                insights_url = f"https://graph.facebook.com/v19.0/{campaign_id}/insights"
                insights_params = {
                    "fields": "date_start,spend,impressions,clicks,actions",
                    "time_range": json.dumps(
                        {"since": start_date.strftime("%Y-%m-%d"), "until": end_date.strftime("%Y-%m-%d")}
                    ),
                    "time_increment": "1",
                    "access_token": access_token,
                }

                insights_res = requests.get(insights_url, params=insights_params, timeout=30)
                insights_json = insights_res.json()

                if "data" not in insights_json or not insights_json["data"]:
                    continue

                for row in insights_json["data"]:
                    date = row["date_start"]
                    costs = float(row.get("spend", 0))
                    impressions = int(row.get("impressions", 0))
                    clicks = int(row.get("clicks", 0))
                    actions = row.get("actions", [])

                    # Keep your existing action mapping (can be improved later)
                    conversions = sum(
                        int(a["value"]) for a in actions
                        if a.get("action_type") == "onsite_conversion.lead_grouped"
                    )
                    sessions = sum(
                        int(a["value"]) for a in actions
                        if a.get("action_type") == "link_click"
                    )

                    cost_per_click = costs / clicks if clicks > 0 else 0
                    cost_per_conversion = costs / conversions if conversions > 0 else 0

                    cursor.execute(
                        """
                        INSERT INTO performanceMetrics (
                            data_source_id, campaign_id, date, costs, impressions, clicks,
                            cost_per_click, conversions, cost_per_conversion, sessions
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (data_source_id, campaign_id, date) DO UPDATE
                        SET costs = EXCLUDED.costs,
                            impressions = EXCLUDED.impressions,
                            clicks = EXCLUDED.clicks,
                            cost_per_click = EXCLUDED.cost_per_click,
                            conversions = EXCLUDED.conversions,
                            cost_per_conversion = EXCLUDED.cost_per_conversion,
                            sessions = EXCLUDED.sessions;
                        """,
                        (
                            data_source_id,
                            campaign_db_id,
                            date,
                            costs,
                            impressions,
                            clicks,
                            cost_per_click,
                            conversions,
                            cost_per_conversion,
                            sessions,
                        ),
                    )

                inserted += 1

        conn.commit()

    return jsonify({"message": f"{inserted} campaigns stored"}), 200


# -----------------------------------------------------------------------------
# Generic reporting endpoints
# -----------------------------------------------------------------------------
@app.route("/filter-performance", methods=["GET"])
def filter_performance():
    time_range = request.args.get("range")
    value = request.args.get("value")

    with get_db() as conn:
        with conn.cursor() as cursor:
            if time_range == "day":
                cursor.execute(
                    """
                    SELECT pm.date, pm.costs, pm.conversions, pm.cost_per_conversion,
                           pm.impressions, pm.clicks, pm.sessions, pm.cost_per_click,
                           ds.source_name
                    FROM performanceMetrics pm
                    JOIN datasources ds ON pm.data_source_id = ds.id
                    WHERE pm.date = %s;
                    """,
                    (value,),
                )
            elif time_range == "range":
                start_date, end_date = (value or "").split("|")
                cursor.execute(
                    """
                    SELECT pm.date, pm.costs, pm.conversions, pm.cost_per_conversion,
                           pm.impressions, pm.clicks, pm.sessions, pm.cost_per_click,
                           ds.source_name
                    FROM performanceMetrics pm
                    JOIN datasources ds ON pm.data_source_id = ds.id
                    WHERE pm.date BETWEEN %s AND %s;
                    """,
                    (start_date, end_date),
                )
            else:
                return jsonify({"error": "Invalid range"}), 400

            rows = cursor.fetchall()

    return jsonify(
        [
            {
                "date": r["date"],
                "costs": r["costs"],
                "conversions": r["conversions"],
                "cost_per_conversion": r["cost_per_conversion"],
                "impressions": r["impressions"],
                "clicks": r["clicks"],
                "sessions": r["sessions"],
                "cost_per_click": r["cost_per_click"],
                "source": r["source_name"],
            }
            for r in rows
        ]
    )

@app.route("/insights", methods=["GET"])
def get_insights():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    # 1) Aggregate to ONE row per day (otherwise you get thousands of rows)
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pm.date,
                    SUM(pm.costs) AS costs,
                    SUM(pm.conversions) AS conversions,
                    CASE
                        WHEN SUM(pm.conversions) > 0 THEN SUM(pm.costs) / SUM(pm.conversions)
                        ELSE 0
                    END AS cost_per_conversion,
                    SUM(pm.impressions) AS impressions,
                    SUM(pm.clicks) AS clicks,
                    SUM(pm.sessions) AS sessions,
                    CASE
                        WHEN SUM(pm.clicks) > 0 THEN SUM(pm.costs) / SUM(pm.clicks)
                        ELSE 0
                    END AS cost_per_click
                FROM performanceMetrics pm
                WHERE pm.date BETWEEN %s AND %s
                GROUP BY pm.date
                ORDER BY pm.date;
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()

    # Return empty list instead of 404 so frontend can handle nicely
    if not rows:
        return jsonify([]), 200

    # 2) Compute summary stats on aggregated daily rows
    total_costs = sum(float(r["costs"] or 0) for r in rows)
    total_conversions = sum(float(r["conversions"] or 0) for r in rows)
    avg_cpa = (total_costs / total_conversions) if total_conversions else 0

    highest_cost_day = max(rows, key=lambda x: float(x["costs"] or 0))
    highest_conv_day = max(rows, key=lambda x: float(x["conversions"] or 0))

    best_cpa_day = None
    rows_with_conv = [r for r in rows if float(r["conversions"] or 0) > 0]
    if rows_with_conv:
        best_cpa_day = min(rows_with_conv, key=lambda x: float(x["cost_per_conversion"] or 0))

    first = rows[0]
    last = rows[-1]
    first_cost = float(first["costs"] or 0)
    last_cost = float(last["costs"] or 0)
    cost_change_pct = ((last_cost - first_cost) / first_cost * 100) if first_cost else 0

    # 3) Build a SMALL set of useful insights (no per-day growth spam)
    insights = [
        {
            "date": highest_cost_day["date"].isoformat(),
            "message": (
                f"Highest costs were on {highest_cost_day['date'].isoformat()} "
                f"with CHF {float(highest_cost_day['costs'] or 0):.2f}."
            ),
        },
        {
            "message": f"Average cost per conversion for the period: CHF {avg_cpa:.2f}."
        },
        {
            "message": (
                f"Cost trend from {first['date'].isoformat()} → {last['date'].isoformat()}: "
                f"{cost_change_pct:+.2f}%."
            )
        },
        {
            "date": highest_conv_day["date"].isoformat(),
            "message": (
                f"Most conversions were on {highest_conv_day['date'].isoformat()} "
                f"({float(highest_conv_day['conversions'] or 0):.0f} conversions)."
            ),
        },
    ]

    if best_cpa_day:
        insights.append(
            {
                "date": best_cpa_day["date"].isoformat(),
                "message": (
                    f"Best cost per conversion was on {best_cpa_day['date'].isoformat()}: "
                    f"CHF {float(best_cpa_day['cost_per_conversion'] or 0):.2f}."
                ),
            }
        )

    return jsonify(insights), 200


@app.route("/aggregated-performance", methods=["GET"])
def get_aggregated_performance():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ds.source_name AS channel,
                    SUM(pm.costs) AS total_costs,
                    SUM(pm.impressions) AS total_impressions,
                    SUM(pm.clicks) AS total_clicks,
                    CASE WHEN SUM(pm.clicks) > 0 THEN SUM(pm.costs) / SUM(pm.clicks) ELSE 0 END AS cost_per_click,
                    SUM(pm.sessions) AS total_sessions,
                    SUM(pm.conversions) AS total_conversions,
                    CASE WHEN SUM(pm.conversions) > 0 THEN SUM(pm.costs) / SUM(pm.conversions) ELSE 0 END AS cost_per_conversion
                FROM performanceMetrics pm
                JOIN datasources ds ON pm.data_source_id = ds.id
                WHERE pm.date BETWEEN %s AND %s
                GROUP BY ds.source_name
                ORDER BY ds.source_name;
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()

    return jsonify(
        [
            {
                "source": r["channel"],
                "costs": float(r["total_costs"]),
                "impressions": r["total_impressions"],
                "clicks": r["total_clicks"],
                "cost_per_click": float(r["cost_per_click"]),
                "sessions": r["total_sessions"],
                "conversions": r["total_conversions"],
                "cost_per_conversion": float(r["cost_per_conversion"]),
            }
            for r in rows
        ]
    )


@app.route("/get-campaigns", methods=["GET"])
def get_campaigns():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ds.source_name AS traffic_source,
                    c.campaign_name,
                    SUM(pm.costs) AS total_costs,
                    SUM(pm.impressions) AS total_impressions,
                    SUM(pm.clicks) AS total_clicks,
                    CASE WHEN SUM(pm.clicks) > 0 THEN SUM(pm.costs) / SUM(pm.clicks) ELSE 0 END AS avg_cpc,
                    SUM(pm.sessions) AS total_sessions,
                    CASE WHEN SUM(pm.sessions) > 0 THEN SUM(pm.costs) / SUM(pm.sessions) ELSE 0 END AS avg_cost_per_session,
                    SUM(pm.conversions) AS total_conversions,
                    CASE WHEN SUM(pm.conversions) > 0 THEN SUM(pm.costs) / SUM(pm.conversions) ELSE 0 END AS avg_cost_per_conversion
                FROM performanceMetrics pm
                JOIN datasources ds ON pm.data_source_id = ds.id
                JOIN campaigns c ON pm.campaign_id = c.id
                WHERE pm.date BETWEEN %s AND %s
                GROUP BY ds.source_name, c.campaign_name
                ORDER BY total_costs DESC;
                """,
                (start_date, end_date),
            )
            rows = cursor.fetchall()

    return jsonify(
        [
            {
                "traffic_source": r[0],
                "campaign_name": r[1],
                "costs": float(r[2]),
                "impressions": r[3],
                "clicks": r[4],
                "cost_per_click": float(r[5]),
                "sessions": r[6],
                "cost_per_session": float(r[7]),
                "conversions": r[8],
                "cost_per_conversion": float(r[9]),
            }
            for r in rows
        ]
    )


if __name__ == "__main__":
    app.run(debug=True)
