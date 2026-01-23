"""
Meta (Facebook) Ads OAuth and data fetching routes for DataPlunge.
"""

import json
from datetime import datetime, timedelta, timezone
import requests
from flask import Blueprint, jsonify, redirect, request, session

from auth import login_required, get_current_user
from config import (
    FRONTEND_BASE_URL,
    META_APP_ID,
    META_APP_SECRET,
    META_REDIRECT_URI,
)
from constants import DATASOURCE_META, META_API_VERSION, META_SCOPES
from db import (
    get_or_create_datasource,
    get_or_create_campaign,
    upsert_performance_metrics,
)

meta_bp = Blueprint('meta', __name__, url_prefix='/meta')


@meta_bp.route("/login")
@login_required
def meta_login():
    """Initiate Meta OAuth."""
    oauth_url = (
        f"https://www.facebook.com/{META_API_VERSION}/dialog/oauth"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&scope={META_SCOPES}"
        "&response_type=code"
        "&state=xyz"
    )
    return redirect(oauth_url)


@meta_bp.route("/callback")
@login_required
def meta_callback():
    """Handle Meta OAuth callback."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    token_url = f"https://graph.facebook.com/{META_API_VERSION}/oauth/access_token"
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


@meta_bp.route("/adaccounts")
@login_required
def meta_adaccounts():
    """Get list of Meta ad accounts."""
    access_token = session.get("meta_token")
    if not access_token:
        return jsonify({"error": "Not logged in"}), 401

    res = requests.get(
        f"https://graph.facebook.com/{META_API_VERSION}/me/adaccounts",
        params={"access_token": access_token, "fields": "id,name,account_status"},
        timeout=30,
    )

    data = res.json()
    if "data" not in data:
        return jsonify({"error": "Could not load ad accounts", "details": data}), 500

    return jsonify(data["data"])


@meta_bp.route("/select-account", methods=["POST"])
@login_required
def select_meta_account():
    """Select a Meta ad account and trigger initial fetch."""
    payload = request.get_json(silent=True) or {}
    account_id = payload.get("account_id")

    if not account_id:
        return jsonify({"error": "account_id is required"}), 400

    session["meta_account_id"] = account_id

    # Trigger fetch immediately
    return fetch_and_store_meta_campaigns()


@meta_bp.route("/fetch-campaigns")
@login_required
def fetch_and_store_meta_campaigns():
    """Fetch Meta campaign data and store in database."""
    access_token = session.get("meta_token")
    account_id = session.get("meta_account_id")

    if not access_token:
        return jsonify({"error": "Not logged in"}), 401
    if not account_id:
        return jsonify({"error": "No Meta ad account selected"}), 400

    user = get_current_user()
    user_id = user['id']

    # Fetch campaigns
    url = f"https://graph.facebook.com/{META_API_VERSION}/{account_id}/campaigns"
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

    # Get or create datasource
    data_source_id = get_or_create_datasource(user_id, DATASOURCE_META)

    # Date range: last 30 days
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=30)

    inserted = 0

    for campaign in campaigns:
        meta_campaign_external_id = str(campaign["id"])
        campaign_name = campaign["name"]

        campaign_db_id = get_or_create_campaign(
            campaign_name=campaign_name,
            data_source_id=data_source_id,
            external_id=meta_campaign_external_id,
        )

        # Fetch insights per campaign
        insights_url = f"https://graph.facebook.com/{META_API_VERSION}/{meta_campaign_external_id}/insights"
        insights_params = {
            "fields": "date_start,spend,impressions,clicks,actions",
            "time_range": json.dumps(
                {
                    "since": start_date.strftime("%Y-%m-%d"),
                    "until": end_date.strftime("%Y-%m-%d"),
                }
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
            costs = float(row.get("spend", 0) or 0)
            impressions = int(row.get("impressions", 0) or 0)
            clicks = int(row.get("clicks", 0) or 0)
            actions = row.get("actions", []) or []

            # Map actions to conversions and sessions
            conversions = sum(
                int(a.get("value", 0) or 0)
                for a in actions
                if a.get("action_type") == "onsite_conversion.lead_grouped"
            )
            sessions = sum(
                int(a.get("value", 0) or 0)
                for a in actions
                if a.get("action_type") == "link_click"
            )

            cost_per_click = costs / clicks if clicks > 0 else 0
            cost_per_conversion = costs / conversions if conversions > 0 else 0

            upsert_performance_metrics(
                data_source_id=data_source_id,
                campaign_id=campaign_db_id,
                date=date,
                costs=costs,
                impressions=impressions,
                clicks=clicks,
                cost_per_click=cost_per_click,
                sessions=sessions,
                conversions=conversions,
                cost_per_conversion=cost_per_conversion,
            )

        inserted += 1

    return jsonify({"message": f"{inserted} campaigns stored"}), 200
