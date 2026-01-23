"""
Google Analytics (GA4) OAuth and data fetching routes for DataPlunge.
"""

from datetime import datetime
from flask import Blueprint, jsonify, redirect, request, session

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

from auth import login_required, get_current_user
from config import (
    FRONTEND_BASE_URL,
    GA_CLIENT_ID,
    GA_CLIENT_SECRET,
    GA_REDIRECT_URI,
    get_google_oauth_client_config,
)
from constants import DATASOURCE_GOOGLE_ANALYTICS, GOOGLE_ANALYTICS_SCOPES
from db import (
    get_or_create_datasource,
    get_or_create_campaign,
    upsert_performance_metrics,
)

google_analytics_bp = Blueprint('google_analytics', __name__, url_prefix='/ga')


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


def get_ga_credentials() -> GACredentials | None:
    """Get GA credentials from session."""
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
    creds.refresh(GARequest())
    return creds


@google_analytics_bp.route("/login")
@login_required
def ga_login():
    """Initiate Google Analytics OAuth."""
    client_config = get_google_oauth_client_config(
        GA_CLIENT_ID,
        GA_CLIENT_SECRET,
        GA_REDIRECT_URI,
    )

    flow = Flow.from_client_config(client_config, scopes=GOOGLE_ANALYTICS_SCOPES)
    flow.redirect_uri = GA_REDIRECT_URI

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    session["ga_state"] = state
    return redirect(auth_url)


@google_analytics_bp.route("/callback")
@login_required
def ga_callback():
    """Handle Google Analytics OAuth callback."""
    client_config = get_google_oauth_client_config(
        GA_CLIENT_ID,
        GA_CLIENT_SECRET,
        GA_REDIRECT_URI,
    )

    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_ANALYTICS_SCOPES,
        state=session.get("ga_state"),
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


@google_analytics_bp.route("/properties")
@login_required
def get_ga_properties():
    """Get list of GA4 properties accessible to the user."""
    creds = get_ga_credentials()
    if not creds:
        return jsonify({"error": "Not authenticated"}), 401

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
            print(f"Failed to load properties for {account.name}: {e}")

    return jsonify(properties)


@google_analytics_bp.route("/fetch-metrics")
@login_required
def fetch_ga_data():
    """Fetch basic GA4 metrics."""
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


@google_analytics_bp.route("/fetch-campaigns")
@login_required
def fetch_ga_campaigns():
    """Fetch GA4 campaign data and store in database."""
    client = get_ga_client()
    if not client:
        return jsonify({"error": "Not authenticated with GA4"}), 401

    property_id = request.args.get("property_id")
    if not property_id:
        return jsonify({"error": "property_id is required"}), 400

    user = get_current_user()
    user_id = user['id']

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

    # Get or create datasource
    data_source_id = get_or_create_datasource(user_id, DATASOURCE_GOOGLE_ANALYTICS)

    for row in response.rows:
        campaign_name = row.dimension_values[1].value or "(not set)"
        raw_date = row.dimension_values[0].value  # YYYYMMDD
        formatted_date = datetime.strptime(raw_date, "%Y%m%d").date()
        sessions_val = int(row.metric_values[0].value or 0)

        campaign_id = get_or_create_campaign(campaign_name=campaign_name)

        upsert_performance_metrics(
            data_source_id=data_source_id,
            campaign_id=campaign_id,
            date=formatted_date,
            sessions=sessions_val,
        )

    return jsonify({"message": "Google Analytics campaign data stored"}), 200
