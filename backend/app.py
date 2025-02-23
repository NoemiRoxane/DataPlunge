from flask import Flask, redirect, request, session, jsonify, g, url_for
import requests
import os
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from google.ads.googleads.client import GoogleAdsClient
from dotenv import load_dotenv
import os



app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")


CORS(app)  # Enable CORS for all routes

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
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT refresh_token FROM google_ads_tokens WHERE customer_id = %s", (customer_id,))
            result = cursor.fetchone()

    if not result:
        print(f"❌ Kein Refresh Token für Customer {customer_id} gefunden. Erneute Anmeldung erforderlich.")
        return None

    refresh_token = result[0]

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
        return new_token_info["access_token"]
    else:
        print("❌ Fehler beim Erneuern des Tokens:", new_token_info)
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

    customer_id = "4008564417"  # Falls dynamisch, aus Session oder DB holen

    if refresh_token: REDACTED

    print(f"🔑 Access Token: {access_token}")

    result = fetch_and_store_campaigns()

    if "error" in result:
        return jsonify(result), 500

    return redirect("http://localhost:3000")





# Step 3: Fetch Google Ads campaign data
@app.route('/google-ads/fetch-campaigns')
def fetch_and_store_campaigns():
    """Fetch Google Ads campaign data and store it in the DB."""

    # ✅ Falls kein Access Token vorhanden, erneuern
    if "access_token" not in session:
        print("❌ Kein Access Token vorhanden. Versuche, es zu erneuern...")
        access_token = refresh_access_token()
        if not access_token:
            return jsonify({"error": "Authentication required. Please log in again."}), 401

    # ✅ `customer_id` direkt definieren (nicht als Argument)
    customer_id = "4008564417"  # Falls dynamisch, session["customer_id"] verwenden

    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    ga_service = client.get_service("GoogleAdsService")

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

            print(f"📊 Campaign: {campaign.name}, Date: {campaign_date}, Impressions: {metrics.impressions}")

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
                        cost_per_conversion = EXCLUDED.cost_per_conversion
                    WHERE performanceMetrics.costs <> EXCLUDED.costs
                    OR performanceMetrics.impressions <> EXCLUDED.impressions
                    OR performanceMetrics.clicks <> EXCLUDED.clicks
                    OR performanceMetrics.cost_per_click <> EXCLUDED.cost_per_click
                    OR performanceMetrics.sessions <> EXCLUDED.sessions
                    OR performanceMetrics.conversions <> EXCLUDED.conversions
                    OR performanceMetrics.cost_per_conversion <> EXCLUDED.cost_per_conversion;
                """, (
                    data_source_id, campaign_id, data["date"], data["costs"], data["impressions"], data["clicks"],
                    data["cost_per_click"], data["sessions"], data["conversions"], data["cost_per_conversion"]
                ))

            print(f"✅ Inserted or updated campaign {data['campaign_name']} for date {data['date']}")

            conn.commit()
            print("✅ Successfully stored campaign data!")

    return jsonify({"message": "Campaign data stored successfully"}), 200



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

    print(f"Rows fetched for {value}: {rows}")

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
    print(f"Filtered data returned: {filtered_data}")
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
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    ds.source_name AS traffic_source,
                    c.campaign_name, 
                    pm.costs, 
                    pm.impressions, 
                    pm.clicks, 
                    pm.cost_per_click, 
                    pm.sessions, 
                    (pm.costs / NULLIF(pm.sessions, 0)) AS cost_per_session,
                    pm.conversions, 
                    pm.cost_per_conversion
                FROM performanceMetrics pm
                JOIN datasources ds ON pm.data_source_id = ds.id
                JOIN campaigns c ON pm.campaign_id = c.id
                ORDER BY pm.costs DESC;
            """)
            campaigns = cursor.fetchall()

    # JSON-Format zurückgeben
    return jsonify([
        {
            "traffic_source": row[0],
            "campaign_name": row[1],
            "costs": row[2],
            "impressions": row[3],
            "clicks": row[4],
            "cost_per_click": row[5],
            "sessions": row[6],
            "cost_per_session": row[7] if row[7] is not None else 0,
            "conversions": row[8],
            "cost_per_conversion": row[9],
        }
        for row in campaigns
    ])


if __name__ == '__main__':

    app.run(debug=True)
