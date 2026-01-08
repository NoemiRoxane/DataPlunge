import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from flask import Flask, redirect, request, session, jsonify, g, url_for
import requests
import json
import os
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta
from flask_session import Session
from google.ads.googleads.client import GoogleAdsClient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from google.auth.transport.requests import Request as GARequest
from google.oauth2.credentials import Credentials as GACredentials
from google_auth_oauthlib.flow import Flow
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import ListPropertiesRequest
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
from urllib.parse import urlencode






import time
import csv

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'dataplunge-session'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_DOMAIN'] = 'localhost'  


Session(app)

CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

DATABASE_URL = "dbname='dataplunge' user='user' host='localhost' password='admin'"

CLIENT_ID = "187329401613-32vdapcu74mb7i9jojheadpit9mkg0kf.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:5000/google-ads/callback"


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# 🛠 Refresh Token speichern
def store_refresh_token(customer_id, refresh_token):
    """Speichert oder aktualisiert das Refresh Token in der Datenbank."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO google_ads_tokens (customer_id, refresh_token)
                VALUES (%s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET refresh_token = EXCLUDED.refresh_token;
                """,
                (customer_id, refresh_token),
            )
            conn.commit()

# 🛠 Refresh Token abrufen
def get_refresh_token(customer_id):
    """Holt das gespeicherte Refresh Token aus der Datenbank."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT refresh_token FROM google_ads_tokens WHERE customer_id = %s;",
                (customer_id,),
            )
            result = cursor.fetchone()
            return result[0] if result else None

def refresh_access_token(customer_id):
    """Holt das gespeicherte Refresh Token aus der DB und erneuert das Access Token."""
    
    refresh_token = get_refresh_token(customer_id)
    if not refresh_token: REDACTED
        return None

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    response = requests.post(token_url, data=token_data)
    new_token_info = response.json()

    if "access_token" in new_token_info:
        print("✅ Access Token erfolgreich erneuert!")
        session["access_token"] = new_token_info["access_token"] 
        return new_token_info["access_token"]
    else:
        print("❌ Fehler beim Erneuern des Tokens:", new_token_info)
        
        # ⬇️ Falls der Refresh Token ungültig ist, zwinge eine erneute Anmeldung
        if new_token_info.get("error") == "invalid_grant":
            print(f"🔄 Refresh Token für {customer_id} ist ungültig. Erneute Anmeldung erforderlich.")
            delete_refresh_token(customer_id)
            return None

        return None

# Funktion zum Löschen ungültiger Refresh Tokens
def delete_refresh_token(customer_id):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM google_ads_tokens WHERE customer_id = %s;", (customer_id,))
            conn.commit()

# 🔥 Customer ID aus Google Ads API abrufen
def get_customer_id_from_api(access_token):
    """Holt die Google Ads Customer ID für den aktuellen Nutzer."""
    url = "https://googleads.googleapis.com/v12/customers:listAccessibleCustomers"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if "resourceNames" in data:
        return [cust.split("/")[-1] for cust in data["resourceNames"]]  # Extrahiere die ID

    print("❌ Fehler beim Abrufen der Customer ID:", data)
    return None


# Step 1: Redirect to Google OAuth
@app.route('/google-ads/login')
def google_ads_login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        f"client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=https://www.googleapis.com/auth/adwords"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(google_auth_url)

# Step 2: Handle OAuth callback
@app.route('/google-ads/callback')
def google_ads_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization failed"}), 400

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(token_url, data=token_data)
    token_json = response.json()

    if "access_token" not in token_json:
        return jsonify({"error": "Token exchange failed", "details": token_json}), 400

    access_token = token_json["access_token"]
    refresh_token = token_json.get("refresh_token")  # 🔥 WICHTIG: Nur falls vorhanden!

    
    # 🔥 **Customer ID aus API holen**
    customer_ids = get_customer_id_from_api(access_token)
    if not customer_ids:
        return jsonify({"error": "Customer ID konnte nicht abgerufen werden"}), 500

    for customer_id in customer_ids:
        if refresh_token: REDACTED
            print(f"✅ Refresh Token gespeichert für {customer_id}: {refresh_token}")
        else:
            print(f"⚠️ Kein Refresh Token für {customer_id} zurückgegeben!")


    result = fetch_and_store_campaigns()

    if "error" in result:
        return jsonify(result), 500

    return redirect("http://localhost:3000")


def get_google_ads_client(customer_id):
    """Lädt dynamisch den Google Ads Client mit dem gespeicherten refresh_token aus der DB."""
    
    refresh_token = get_refresh_token(customer_id)  # Holt Token aus DB
    if not refresh_token: REDACTED
        return None

    try:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )

        # Token erneuern
        creds.refresh(Request())

        # Google Ads Client mit dynamischen Credentials laden
        client = GoogleAdsClient.load_from_dict({
            "developer_token": "Z0JS-BxTiTPDgbOH2KwcMA",
            "use_proto_plus": True,
            "login_customer_id": customer_id,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token,  # Direktes Einfügen des Tokens
        })

        return client
    except Exception as e:
        print(f"❌ Fehler beim Laden des Google Ads Clients für {customer_id}: {e}")
        return None

def get_customer_id_from_db():
    """Holt die gespeicherte Google Ads Customer ID aus der Datenbank."""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT customer_id FROM google_ads_tokens LIMIT 1;")  # Falls du nur einen speicherst
            result = cursor.fetchone()
            return result[0] if result else None



# Step 3: Fetch Google Ads campaign data
@app.route('/google-ads/fetch-campaigns')
def fetch_and_store_campaigns():
    """Fetch Google Ads campaign data and store it in the DB."""
    
    # 🔥 Customer ID aus Session oder DB holen
    customer_id = session.get("customer_id") or get_customer_id_from_db()
    if not customer_id:
        return jsonify({"error": "Customer ID nicht gefunden"}), 400

    # ✅ Lade den Google Ads Client mit OAuth2-Credentials
    client = get_google_ads_client(customer_id)
    if not client:
        return jsonify({"error": "Google Ads Client konnte nicht erstellt werden."}), 500

    # ✅ Google Ads Service abrufen
    try:
        ga_service = client.get_service("GoogleAdsService")
    except Exception as e:
        print(f"❌ Fehler beim Abrufen des Google Ads Service: {e}")
        return jsonify({"error": "Google Ads Client Fehler", "details": str(e)}), 500

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

    print(f"🛠 Fetching campaigns for customer: {customer_id}")

    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)
    except Exception as e:
        print(f"❌ API-Fehler: {e}")
        return jsonify({"error": "Google Ads API request failed", "details": str(e)}), 500

    campaign_data = []
    for batch in response:
        for row in batch.results:
            campaign = row.campaign
            metrics = row.metrics
            campaign_date = row.segments.date

            # print(f"📊 Campaign: {campaign.name}, Date: {campaign_date}, Impressions: {metrics.impressions}")

            campaign_data.append({
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "date": campaign_date,
                "costs": metrics.cost_micros / 1e6,
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "cost_per_click": (metrics.average_cpc / 1e6) if metrics.average_cpc else 0,
                "sessions": metrics.interactions if metrics.interactions else 0,
                "conversions": metrics.conversions if metrics.conversions else 0,
                "cost_per_conversion": (metrics.cost_per_conversion / 1e6) if metrics.cost_per_conversion else 0
            })

    if not campaign_data:
        print("❌ No campaigns found!")
        return jsonify({"error": "No campaigns found"}), 404

    print(f"💾 Storing {len(campaign_data)} campaigns in database...")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM datasources WHERE source_name = 'Google Ads' LIMIT 1;")
            data_source_id = cursor.fetchone()
            if data_source_id:
                data_source_id = data_source_id[0]
            else:
                print("❌ No data_source_id found for 'Google Ads'")
                return jsonify({"error": "No data_source_id found"}), 500

            for data in campaign_data:
                print(f"📌 Writing Campaign: {data['campaign_name']} for Date: {data['date']}")

                cursor.execute("SELECT id FROM campaigns WHERE id = %s LIMIT 1;", (data["campaign_id"],))
                campaign_id = cursor.fetchone()

                if not campaign_id:
                    print(f"🚀 Inserting new campaign: {data['campaign_name']}")
                    cursor.execute("INSERT INTO campaigns (id, campaign_name) VALUES (%s, %s) RETURNING id;",
                                   (data["campaign_id"], data["campaign_name"]))
                    campaign_id = cursor.fetchone()[0]
                else:
                    campaign_id = campaign_id[0]

                print(f"💾 Writing performance data for {data['campaign_name']} on {data['date']}")

                cursor.execute("""
                    INSERT INTO performanceMetrics (
                        data_source_id, campaign_id, date, costs, impressions, clicks, cost_per_click, sessions, conversions, cost_per_conversion
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (data_source_id, campaign_id, date) DO UPDATE
                    SET costs = EXCLUDED.costs, 
                        impressions = EXCLUDED.impressions, 
                        clicks = EXCLUDED.clicks,
                        cost_per_click = EXCLUDED.cost_per_click, 
                        sessions = EXCLUDED.sessions,
                        conversions = EXCLUDED.conversions,
                        cost_per_conversion = EXCLUDED.cost_per_conversion;
                """, (
                    data_source_id, campaign_id, data["date"], data["costs"], data["impressions"], data["clicks"],
                    data["cost_per_click"], data["sessions"], data["conversions"], data["cost_per_conversion"]
                ))

            print(f"✅ Inserted or updated campaign {data['campaign_name']} for date {data['date']}")

            conn.commit()
            print("✅ Successfully stored campaign data!")

    return jsonify({"message": "Campaign data stored successfully"}), 200


def get_ga_client():
    creds_data = session.get("ga_token")
    if not creds_data:
        print("❌ Kein GA-Token in der Session.")
        return None

    creds = GACredentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"]
    )

    if creds.expired and creds.refresh_token: REDACTED

    return BetaAnalyticsDataClient(credentials=creds)

@app.route("/ga/fetch-metrics")
def fetch_ga_data():
    client = get_ga_client()
    if not client:
        return jsonify({"error": "Nicht authentifiziert mit GA4"}), 401

    PROPERTY_ID = request.args.get("property_id")
    if not PROPERTY_ID:
        return jsonify({"error": "property_id ist erforderlich"}), 400


    request_obj = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[{"name": "date"}],
        metrics=[
            {"name": "sessions"},
            {"name": "totalUsers"},
            {"name": "bounceRate"},
        ],
        date_ranges=[{"start_date": "30daysAgo", "end_date": "today"}],
    )

    response = client.run_report(request=request_obj)

    result = []
    for row in response.rows:
        result.append({
            "date": row.dimension_values[0].value,
            "sessions": row.metric_values[0].value,
            "users": row.metric_values[1].value,
            "bounce_rate": row.metric_values[2].value,
        })

    return jsonify(result)


@app.route("/ga/login")
def ga_login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GA_CLIENT_ID"),
                "client_secret": os.getenv("GA_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GA_REDIRECT_URI")],
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/analytics.edit",
            "https://www.googleapis.com/auth/analytics.manage.users",
            "https://www.googleapis.com/auth/analytics"
        ]
    )
    flow.redirect_uri = os.getenv("GA_REDIRECT_URI")

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return redirect(auth_url)


@app.route("/ga/properties")
def get_ga_properties():
    print("📦 SESSION:", dict(session))  # <--- NEU
    creds_data = session.get("ga_token")
    ...

    if not creds_data:
        return jsonify({"error": "Nicht authentifiziert"}), 401

    creds = GACredentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"]
    )
    creds.refresh(GARequest())
    client = AnalyticsAdminServiceClient(credentials=creds)

    all_properties = []
    try:
        accounts = client.list_accounts()
    except Exception as e:
        return jsonify({"error": f"Fehler beim Laden der Accounts: {e}"}), 500

    for account in accounts:
        account_id = account.name.split("/")[-1]
        try:
            request = ListPropertiesRequest(filter=f"parent:accounts/{account_id}")
            props = client.list_properties(request=request)
            for prop in props:
                all_properties.append({
                    "property_id": prop.name.split("/")[-1],
                    "display_name": prop.display_name,
                    "time_zone": prop.time_zone
                })
        except Exception as e:
            print(f"⚠️ Fehler beim Laden von Properties für {account.name}: {e}")

    return jsonify(all_properties)


@app.route("/ga/callback")
def ga_callback():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GA_CLIENT_ID"),
                "client_secret": os.getenv("GA_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GA_REDIRECT_URI")],
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/analytics.edit",
            "https://www.googleapis.com/auth/analytics.manage.users",
            "https://www.googleapis.com/auth/analytics"
        ]
    )
    flow.redirect_uri = os.getenv("GA_REDIRECT_URI")

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials

    # Speichere Tokens temporär in Session
    session["ga_token"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

    print("✅ GA-Token gespeichert in Session!")

    # 🔁 Nach dem Login zurück zur richtigen React-Seite
    return redirect("http://localhost:3000/connect/google-analytics?ga_ready=true")



@app.route("/ga/fetch-campaigns")
def fetch_ga_campaigns():
    client = get_ga_client()
    if not client:
        return jsonify({"error": "Nicht authentifiziert mit GA4"}), 401

    property_id = request.args.get("property_id")
    if not property_id:
        return jsonify({"error": "property_id ist erforderlich"}), 400

    # Run GA4 report grouped by date and campaign name
    request_obj = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date"), Dimension(name="sessionCampaignName")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="bounceRate"),
        ],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    )

    try:
        response = client.run_report(request=request_obj)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Abrufen der GA-Daten: {e}"}), 500

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Finde data_source_id für Google Analytics
            cursor.execute("SELECT id FROM datasources WHERE source_name = 'Google Analytics' LIMIT 1;")
            ds_row = cursor.fetchone()
            if not ds_row:
                return jsonify({"error": "Google Analytics nicht in der datasources-Tabelle gefunden"}), 500
            data_source_id = ds_row[0]

            for row in response.rows:
                campaign_name = row.dimension_values[1].value or "(not set)"
                campaign_date = row.dimension_values[0].value  # Format: YYYYMMDD
                formatted_date = datetime.strptime(campaign_date, "%Y%m%d").date()

                sessions = int(row.metric_values[0].value or 0)
                users = int(row.metric_values[1].value or 0)
                bounce_rate = float(row.metric_values[2].value or 0)

                # 🔍 Kampagne existiert bereits?
                cursor.execute("SELECT id FROM campaigns WHERE campaign_name = %s LIMIT 1;", (campaign_name,))
                existing = cursor.fetchone()
                if existing:
                    campaign_id = existing[0]
                else:
                    cursor.execute("INSERT INTO campaigns (campaign_name) VALUES (%s) RETURNING id;", (campaign_name,))
                    campaign_id = cursor.fetchone()[0]

                # 📥 Insert or Update performance metrics
                cursor.execute("""
                    INSERT INTO performanceMetrics (
                        data_source_id, campaign_id, date, sessions
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (data_source_id, campaign_id, date) DO UPDATE
                    SET sessions = EXCLUDED.sessions;
                """, (data_source_id, campaign_id, formatted_date, sessions))

    conn.commit()
    print("✅ Google Analytics Kampagnendaten erfolgreich gespeichert!")
    return jsonify({"message": "Google Analytics Kampagnendaten gespeichert"}), 200


@app.route("/meta/login")
def meta_login():
    meta_app_id = os.getenv("META_APP_ID")
    redirect_uri = os.getenv("META_REDIRECT_URI")

    if not meta_app_id or not redirect_uri:
        return "❌ META_APP_ID oder META_REDIRECT_URI nicht gesetzt", 500

    oauth_url = (
        "https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={meta_app_id}"
        f"&redirect_uri={redirect_uri}"
        "&scope=ads_read,ads_management"
        "&response_type=code"
        "&state=xyz"
    )
    return redirect(oauth_url)



@app.route('/meta/callback')
def meta_callback():
    code = request.args.get("code")
    redirect_uri = os.getenv("META_REDIRECT_URI")  # sichergehen, dass es gesetzt ist!

    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": os.getenv("META_APP_ID"),
        "client_secret": os.getenv("META_APP_SECRET"),
        "redirect_uri": redirect_uri,
        "code": code
    }

    response = requests.get(token_url, params=params)
    token_info = response.json()

    if "access_token" not in token_info:
        return jsonify({"error": "Token konnte nicht abgerufen werden", "details": token_info}), 400

    session["meta_token"] = token_info["access_token"]
    print("✅ Meta Access Token gespeichert in Session!")

    # ➔ redirect zur Wizard-Seite (analog GA)
    return redirect("http://localhost:3000/connect/meta?meta_ready=true")


@app.route('/meta/adaccounts')
def meta_adaccounts():
    access_token = session.get("meta_token")
    if not access_token:
        return jsonify({"error": "Nicht eingeloggt"}), 401

    res = requests.get(
        "https://graph.facebook.com/v19.0/me/adaccounts",
        params={"access_token": access_token, "fields": "id,name,account_status"}
    )
    
    accounts_data = res.json()
    if "data" not in accounts_data:
        print("❌ Fehler beim Laden der Ad Accounts:", accounts_data)
        return jsonify({"error": "Accounts konnten nicht geladen werden", "details": accounts_data}), 500

    print("📡 Meta Accounts geladen:", accounts_data["data"])
    return jsonify(accounts_data["data"])

@app.route('/meta/select-account', methods=["POST"])
def select_meta_account():
    data = request.get_json()
    account_id = data.get("account_id")

    if not account_id:
        return jsonify({"error": "account_id fehlt"}), 400

    session["meta_account_id"] = account_id
    print(f"✅ Meta Account {account_id} gespeichert in Session")

    access_token = session.get("meta_token")
    if not access_token:
        print("⚠️ Kein Meta Access Token in Session")
        return jsonify({"error": "Kein Access Token"}), 401

    # 🎯 Speichern nach Auswahl
    fetch_and_store_meta_campaigns()

    return jsonify({"message": f"Meta Account {account_id} gespeichert & Daten geladen"}), 200



@app.route('/meta/fetch-campaigns')
def fetch_and_store_meta_campaigns():
    access_token = session.get("meta_token")
    account_id = session.get("meta_account_id")
    if not access_token:
        return jsonify({"error": "Nicht eingeloggt"}), 401
    if not account_id:
        return jsonify({"error": "Kein Meta-Account ausgewählt"}), 400

    # Kampagnen abrufen
    url = f"https://graph.facebook.com/v19.0/{account_id}/campaigns"
    params = {
    "fields": "id,name,status",
    "effective_status": '["ACTIVE","PAUSED"]',
    "access_token": access_token
    }

    response = requests.get(url, params=params)
    campaigns_data = response.json()

    if "data" not in campaigns_data or not campaigns_data["data"]:
        print(f"⚠️ Keine Kampagnen gefunden oder Fehler: {campaigns_data}")
        return jsonify({"error": "Keine Kampagnen gefunden", "details": campaigns_data}), 404

    campaigns = campaigns_data["data"]
    inserted_rows = []

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Hole data_source_id für Meta
            cursor.execute("SELECT id FROM datasources WHERE source_name = 'Meta' LIMIT 1;")
            ds_row = cursor.fetchone()
            if not ds_row:
                return jsonify({"error": "Meta nicht in datasources gefunden"}), 500
            data_source_id = ds_row[0]

            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=30)

            for campaign in campaigns:
                campaign_id = int(campaign["id"])
                campaign_name = campaign["name"]

                print(f"📌 Verarbeite Kampagne {campaign_id}: {campaign_name}")

                # Kampagne speichern oder aktualisieren
                cursor.execute("SELECT id FROM campaigns WHERE id = %s LIMIT 1;", (campaign_id,))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute("INSERT INTO campaigns (id, campaign_name) VALUES (%s, %s) RETURNING id;",
                                   (campaign_id, campaign_name))
                    campaign_db_id = cursor.fetchone()[0]
                else:
                    campaign_db_id = existing[0]

                # Insights abrufen
                insights_url = f"https://graph.facebook.com/v19.0/{campaign_id}/insights"
                insights_params = {
                    "fields": "date_start,spend,impressions,clicks,actions",
                    "time_range": json.dumps({
                        "since": start_date.strftime("%Y-%m-%d"),
                        "until": end_date.strftime("%Y-%m-%d")
                    }),
                    "time_increment": "1",
                    "access_token": access_token
                }
                insights_res = requests.get(insights_url, params=insights_params)
                insights = insights_res.json()
                print(f"📊 Actions für Kampagne {campaign_id}:")
                for row in insights.get("data", []):
                    actions = row.get("actions", [])
                    if actions:
                        print(json.dumps(actions, indent=2))
                    else:
                        print("Keine actions vorhanden.")


                if "data" not in insights or not insights["data"]:
                    print(f"⚠️ Keine Insights für Kampagne {campaign_id}: {insights}")
                    continue

               # Performance-Daten speichern
                for row in insights["data"]:
                    date = row["date_start"]
                    costs = float(row.get("spend", 0))
                    impressions = int(row.get("impressions", 0))
                    clicks = int(row.get("clicks", 0))
                    actions = row.get("actions", [])

                    conversions = sum(int(a["value"]) for a in actions if a["action_type"] == "onsite_conversion.lead_grouped")
                    sessions = sum(int(a["value"]) for a in actions if a["action_type"] == "link_click")

                    cost_per_click = costs / clicks if clicks > 0 else 0
                    cost_per_conversion = costs / conversions if conversions > 0 else 0

                    cursor.execute("""
                        INSERT INTO performanceMetrics (
                            data_source_id, campaign_id, date, costs, impressions, clicks, cost_per_click,
                            conversions, cost_per_conversion, sessions
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (data_source_id, campaign_id, date) DO UPDATE
                        SET costs = EXCLUDED.costs,
                            impressions = EXCLUDED.impressions,
                            clicks = EXCLUDED.clicks,
                            cost_per_click = EXCLUDED.cost_per_click,
                            conversions = EXCLUDED.conversions,
                            cost_per_conversion = EXCLUDED.cost_per_conversion,
                            sessions = EXCLUDED.sessions;
                    """, (
                        data_source_id, campaign_db_id, date, costs, impressions, clicks,
                        cost_per_click, conversions, cost_per_conversion, sessions
                    ))


                inserted_rows.append({"campaign_id": campaign_db_id, "campaign_name": campaign_name})

            conn.commit()

    print(f"✅ Meta-Kampagnen & Performance gespeichert: {len(inserted_rows)}")
    return jsonify({"message": f"{len(inserted_rows)} Kampagnen gespeichert", "data": inserted_rows}), 200


@app.route('/meta/save-account')
def save_meta_account():
    account_id = request.args.get("account_id")
    if not account_id:
        return jsonify({"error": "account_id ist erforderlich"}), 400

    session["meta_account_id"] = account_id
    print(f"✅ Meta Account ID {account_id} gespeichert in Session!")
    return jsonify({"message": f"Account {account_id} gespeichert"})



"""@app.route("/ga/fetch-campaigns")
def fetch_ga_campaigns():
    client = get_ga_client()
    if not client:
        return jsonify({"error": "Nicht authentifiziert mit GA4"}), 401

    property_id = request.args.get("property_id")
    if not property_id:
        return jsonify({"error": "property_id ist erforderlich"}), 400

    # Run GA4 report grouped by date and campaign name
    request_obj = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date"), Dimension(name="sessionCampaignName")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="bounceRate"),
        ],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    )

    try:
        response = client.run_report(request=request_obj)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Abrufen der GA-Daten: {e}"}), 500

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Finde data_source_id für Google Analytics
            cursor.execute("SELECT id FROM datasources WHERE source_name = 'Google Analytics' LIMIT 1;")
            ds_row = cursor.fetchone()
            if not ds_row:
                return jsonify({"error": "Google Analytics nicht in der datasources-Tabelle gefunden"}), 500
            data_source_id = ds_row[0]

            for row in response.rows:
                campaign_name = row.dimension_values[1].value or "(not set)"
                campaign_date = row.dimension_values[0].value  # Format: YYYYMMDD
                formatted_date = datetime.strptime(campaign_date, "%Y%m%d").date()

                sessions = int(row.metric_values[0].value or 0)
                users = int(row.metric_values[1].value or 0)
                bounce_rate = float(row.metric_values[2].value or 0)

                # 🔍 Kampagne existiert bereits?
                cursor.execute("SELECT id FROM campaigns WHERE campaign_name = %s LIMIT 1;", (campaign_name,))
                existing = cursor.fetchone()
                if existing:
                    campaign_id = existing[0]
                else:
                    cursor.execute("INSERT INTO campaigns (campaign_name) VALUES (%s) RETURNING id;", (campaign_name,))
                    campaign_id = cursor.fetchone()[0]

                # 📥 Insert or Update performance metrics
                

    conn.commit()
    print("✅ Google Analytics Kampagnendaten erfolgreich gespeichert!")
    return jsonify({"message": "Google Analytics Kampagnendaten gespeichert"}), 200 """



@app.route('/filter-performance', methods=['GET'])
def filter_performance():
    time_range = request.args.get('range')
    value = request.args.get('value')
    print(f"Received value from frontend: {value}")  # Debugging

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Determine if filtering by a specific day or a range
            if time_range == 'day':
                query = """
                    SELECT pm.date, pm.costs, pm.conversions, pm.cost_per_conversion, pm.impressions, pm.clicks, pm.sessions, pm.cost_per_click, ds.source_name
                    FROM PerformanceMetrics pm
                    JOIN DataSources ds ON pm.data_source_id = ds.id
                    WHERE pm.date = %s;
                """
                cursor.execute(query, (value,))
            elif time_range == 'range':
                start_date, end_date = value.split('|')
                query = """
                    SELECT pm.date, pm.costs, pm.conversions, pm.cost_per_conversion, pm.impressions, pm.clicks, pm.sessions, pm.cost_per_click, ds.source_name
                    FROM PerformanceMetrics pm
                    JOIN DataSources ds ON pm.data_source_id = ds.id
                    WHERE pm.date BETWEEN %s AND %s;
                """
                cursor.execute(query, (start_date, end_date))
            else:
                print("Invalid time range.")
                return jsonify({'error': 'Invalid time range'}), 400

            rows = cursor.fetchall()

    # print(f"Rows fetched for {value}: {rows}")

    if not rows:
        print("No data found for the given range.")
        return jsonify([])

    filtered_data = [
        {
            'date': row['date'],
            'costs': row['costs'],
            'conversions': row['conversions'],
            'cost_per_conversion': row['cost_per_conversion'],
            'impressions': row['impressions'],
            'clicks': row['clicks'],
            'sessions': row['sessions'],
            'cost_per_click': row['cost_per_click'],
            'source': row['source_name'],
        }
        for row in rows
    ]
    # print(f"Filtered data returned: {filtered_data}")
    return jsonify(filtered_data)


@app.route('/insights', methods=['GET'])
def get_insights():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Check if both start and end dates are provided
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date must be provided'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            query = '''
                SELECT date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click
                FROM PerformanceMetrics
                WHERE date BETWEEN %s AND %s
                ORDER BY date
            '''
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()

    if not rows:
        return jsonify({'error': 'No data available for the given dates'}), 404

    # Calculate insights
    insights = []
    total_costs = sum(row['costs'] for row in rows)
    total_conversions = sum(row['conversions'] for row in rows)
    average_cost_per_conversion = total_costs / total_conversions if total_conversions > 0 else 0

    # Highest costs
    highest_cost = max(rows, key=lambda x: x['costs'])
    insights.append({
        'date': highest_cost['date'].isoformat(),
        'message': f'Highest costs were on {highest_cost["date"].isoformat()} with CHF {highest_cost["costs"]:.2f}.'
    })

    # Growth calculation
    if len(rows) > 1:
        prev_day = rows[0]
        for current_day in rows[1:]:
            growth_rate = ((current_day['costs'] - prev_day['costs']) / prev_day['costs'] * 100) if prev_day['costs'] else 0
            insights.append({
                'date': current_day['date'].isoformat(),
                'message': f'Costs grew by {growth_rate:.2f}% on {current_day["date"].isoformat()} compared to {prev_day["date"].isoformat()}.'
            })
            prev_day = current_day

    # Average cost per conversion
    insights.append({
        'message': f'Average cost per conversion for the period: CHF {average_cost_per_conversion:.2f}.'
    })

    return jsonify(insights)


@app.route('/aggregated-performance', methods=['GET'])
def get_aggregated_performance():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            # Aggregating data by source in the given date range
            query = '''
                SELECT
                    ds.source_name AS channel,
                    SUM(pm.costs) AS total_costs,
                    SUM(pm.impressions) AS total_impressions,
                    SUM(pm.clicks) AS total_clicks,
                    CASE WHEN SUM(pm.clicks) > 0 THEN SUM(pm.costs) / SUM(pm.clicks) ELSE 0 END AS cost_per_click,
                    SUM(pm.sessions) AS total_sessions,
                    SUM(pm.conversions) AS total_conversions,
                    CASE WHEN SUM(pm.conversions) > 0 THEN SUM(pm.costs) / SUM(pm.conversions) ELSE 0 END AS cost_per_conversion
                FROM PerformanceMetrics pm
                JOIN DataSources ds ON pm.data_source_id = ds.id
                WHERE pm.date BETWEEN %s AND %s
                GROUP BY ds.source_name
                ORDER BY ds.source_name;
            '''
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()

    # Formatting the response
    data = [
        {
            'source': row['channel'],
            'costs': float(row['total_costs']),
            'impressions': row['total_impressions'],
            'clicks': row['total_clicks'],
            'cost_per_click': float(row['cost_per_click']),
            'sessions': row['total_sessions'],
            'conversions': row['total_conversions'],
            'cost_per_conversion': float(row['cost_per_conversion']),
        }
        for row in rows
    ]

    return jsonify(data)

@app.route("/get-campaigns", methods=["GET"])
def get_campaigns():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
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
            """, (start_date, end_date))

            campaigns = cursor.fetchall()

    return jsonify([
        {
            "traffic_source": row[0],
            "campaign_name": row[1],
            "costs": float(row[2]),
            "impressions": row[3],
            "clicks": row[4],
            "cost_per_click": float(row[5]),
            "sessions": row[6],
            "cost_per_session": float(row[7]),
            "conversions": row[8],
            "cost_per_conversion": float(row[9]),
        }
        for row in campaigns
    ])


if __name__ == '__main__':

    app.run(debug=True)
