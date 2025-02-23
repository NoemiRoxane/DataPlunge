from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import psycopg2
from psycopg2.extras import DictCursor

# ✅ Load Google Ads API client
client = GoogleAdsClient.load_from_storage("google-ads.yaml")

# ✅ DB Verbindung
DATABASE_URL = "dbname='dataplunge' user='user' host='localhost' password='admin'"

def get_db():
    """Verbindet mit der Datenbank und gibt die Verbindung zurück."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)

def fetch_and_store_campaigns(customer_id):
    """Fetch Google Ads campaign data (last 7 days) and store it in DB."""
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
        WHERE segments.date DURING LAST_7_DAYS
        ORDER BY campaign.id, segments.date
    """

    print(f"✅ Fetching campaigns for customer: {customer_id}")

    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)

        campaign_data = []
        for batch in response:
            for row in batch.results:
                campaign = row.campaign
                metrics = row.metrics

                cost = metrics.cost_micros / 1e6
                cost_per_click = metrics.average_cpc / 1e6 if metrics.average_cpc else 0
                sessions = metrics.interactions if metrics.interactions else 0
                conversions = metrics.conversions if metrics.conversions else 0
                cost_per_conversion = metrics.cost_per_conversion / 1e6 if metrics.cost_per_conversion else 0

                campaign_data.append({
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "date": row.segments.date,
                    "costs": cost,
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "cost_per_click": cost_per_click,
                    "sessions": sessions,
                    "conversions": conversions,
                    "cost_per_conversion": cost_per_conversion
                })

                print(f"📢 {campaign.name} | {metrics.impressions} impressions, {metrics.clicks} clicks")

        print(f"💾 Speichere {len(campaign_data)} Kampagnen in die Datenbank...")
        store_campaign_data(campaign_data)

    except GoogleAdsException as ex:
        print(f"\n❌ Google Ads API Error: {ex}")
        for error in ex.failure.errors:
            print(f"Error message: {error.message}")
            if error.location:
                for field in error.location.field_path_elements:
                    print(f"Field: {field.field_name}")
        return None

def store_campaign_data(campaign_data):
    """Store campaign data into the PostgreSQL database."""
    with get_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute("SELECT id FROM datasources WHERE source_name = 'Google Ads' LIMIT 1;")
            data_source_id = cursor.fetchone()

            if not data_source_id:
                print("❌ Kein data_source_id für 'Google Ads' gefunden!")
                return
            data_source_id = data_source_id[0]

            for data in campaign_data:
                cursor.execute("SELECT id FROM campaigns WHERE id = %s LIMIT 1;", (data["campaign_id"],))
                campaign_id = cursor.fetchone()

                if not campaign_id:
                    print(f"🚀 Inserting new campaign: {data['campaign_name']}")
                    cursor.execute("INSERT INTO campaigns (id, campaign_name) VALUES (%s, %s) RETURNING id;",
                                   (data["campaign_id"], data["campaign_name"]))
                    campaign_id = cursor.fetchone()[0]
                else:
                    campaign_id = campaign_id[0]
                    print(f"⚡ Campaign already exists with ID: {campaign_id}")

                # 🔹 Speichere die Performance-Daten mit ON CONFLICT, um doppelte Einträge zu vermeiden
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

            conn.commit()
            print("✅ Erfolgreich gespeichert!")

# ✅ Replace with your test customer ID
TEST_CUSTOMER_ID = "4008564417"

# Run the script
fetch_and_store_campaigns(TEST_CUSTOMER_ID)
