"""
Google Ads OAuth and data fetching routes for DataPlunge.
"""

import requests
from flask import Blueprint, jsonify, redirect, request, session

from google.ads.googleads.client import GoogleAdsClient
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials as GoogleCredentials

from auth import login_required, get_current_user
from config import (
    FRONTEND_BASE_URL,
    GOOGLE_ADS_CLIENT_ID,
    GOOGLE_ADS_CLIENT_SECRET,
    GOOGLE_ADS_REDIRECT_URI,
    GOOGLE_ADS_DEVELOPER_TOKEN,
)
from constants import DATASOURCE_GOOGLE_ADS, GOOGLE_ADS_API_VERSION
from db import (
    get_db,
    store_google_ads_refresh_token,
    get_google_ads_refresh_token,
    delete_google_ads_refresh_token,
    get_google_ads_customer_id,
    get_or_create_datasource,
    get_or_create_campaign,
    upsert_performance_metrics,
)

google_ads_bp = Blueprint('google_ads', __name__, url_prefix='/google-ads')


def refresh_google_ads_access_token(customer_id: str, user_id: int) -> str | None:
    """Refresh a Google OAuth access token using stored refresh token."""
    refresh_token = get_google_ads_refresh_token(customer_id, user_id)
    if not refresh_token:
        print(f"No refresh token found for customer {customer_id} and user {user_id}.")
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

    # If refresh token is invalid, remove it so the user must re-auth
    if token_json.get("error") == "invalid_grant":
        print(f"Refresh token invalid for customer {customer_id}. Removing from DB.")
        delete_google_ads_refresh_token(customer_id, user_id)

    print(f"Failed to refresh access token: {token_json}")
    return None


def get_customer_ids_from_api(access_token: str) -> list[str]:
    """Get accessible customer IDs from Google Ads API."""
    url = f"https://googleads.googleapis.com/{GOOGLE_ADS_API_VERSION}/customers:listAccessibleCustomers"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": GOOGLE_ADS_DEVELOPER_TOKEN,
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=30)

    if not response.ok:
        print(f"Google Ads API ERROR - Status: {response.status_code}, Body: {response.text[:2000]}")
        response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type.lower():
        raise ValueError("Expected JSON but got non-JSON response from Google Ads API")

    data = response.json()
    resource_names = data.get("resourceNames", [])
    customer_ids = [rn.split("/")[1] for rn in resource_names if rn.startswith("customers/")]

    return customer_ids


def get_google_ads_client(customer_id: str, user_id: int) -> GoogleAdsClient | None:
    """Create GoogleAdsClient using refresh token from DB."""
    refresh_token = get_google_ads_refresh_token(customer_id, user_id)
    if not refresh_token:
        print(f"No refresh token found for customer {customer_id} and user {user_id}.")
        return None

    # Verify token can be refreshed
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
        print(f"Google OAuth refresh failed for customer {customer_id}: {e}")
        return None

    try:
        return GoogleAdsClient.load_from_dict(
            {
                "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
                "use_proto_plus": True,
                "login_customer_id": customer_id,
                "client_id": GOOGLE_ADS_CLIENT_ID,
                "client_secret": GOOGLE_ADS_CLIENT_SECRET,
                "refresh_token": refresh_token,
            }
        )
    except Exception as e:
        print(f"Failed to build GoogleAdsClient for {customer_id}: {e}")
        return None


@google_ads_bp.route("/login")
@login_required
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


@google_ads_bp.route("/callback")
@login_required
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
        }), 400

    if "access_token" not in token_json:
        return jsonify({"error": "Token exchange failed", "details": token_json}), 400

    access_token = token_json["access_token"]
    refresh_token = token_json.get("refresh_token")

    customer_ids = get_customer_ids_from_api(access_token)
    if not customer_ids:
        return jsonify({"error": "Failed to fetch customer IDs"}), 500

    user = get_current_user()
    user_id = user['id']

    # Store refresh token per customer
    for cid in customer_ids:
        if refresh_token:
            store_google_ads_refresh_token(cid, refresh_token, user_id)
            print(f"Stored refresh token for customer {cid} and user {user_id}.")

    # Store one customer_id in session as a default
    session["customer_id"] = customer_ids[0]

    # Create datasource for user
    get_or_create_datasource(user_id, DATASOURCE_GOOGLE_ADS)

    # Trigger initial fetch
    fetch_and_store_campaigns()

    # Redirect user back to main page
    return redirect(FRONTEND_BASE_URL)


@google_ads_bp.route("/fetch-campaigns")
@login_required
def fetch_and_store_campaigns():
    """Fetch Google Ads campaign performance and store it in DB."""
    user = get_current_user()
    user_id = user['id']

    customer_id = session.get("customer_id") or get_google_ads_customer_id(user_id)
    if not customer_id:
        return jsonify({"error": "Customer ID not found"}), 400

    client = get_google_ads_client(customer_id, user_id)
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

    # Get or create datasource
    data_source_id = get_or_create_datasource(user_id, DATASOURCE_GOOGLE_ADS)

    for row in campaign_rows:
        campaign_id = get_or_create_campaign(
            campaign_name=row["campaign_name"],
            campaign_id=row["campaign_id"]
        )

        upsert_performance_metrics(
            data_source_id=data_source_id,
            campaign_id=campaign_id,
            date=row["date"],
            costs=row["costs"],
            impressions=row["impressions"],
            clicks=row["clicks"],
            cost_per_click=row["cost_per_click"],
            sessions=row["sessions"],
            conversions=row["conversions"],
            cost_per_conversion=row["cost_per_conversion"],
        )

    return jsonify({"message": "Campaign data stored successfully"}), 200
