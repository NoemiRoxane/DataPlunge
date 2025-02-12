from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# ✅ Load Google Ads API client
client = GoogleAdsClient.load_from_storage("google-ads.yaml")

def fetch_campaigns(customer_id):
    """Fetch detailed Google Ads campaign data."""
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.average_cpc,
            metrics.interactions,  -- Proxy für Sessions
            metrics.conversions,
            metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY campaign.id
    """

    try:
        # ✅ Fetch campaign data
        response = ga_service.search_stream(customer_id=customer_id, query=query)

        print("\n=== Google Ads Campaigns ===")
        for batch in response:
            for row in batch.results:
                campaign = row.campaign
                metrics = row.metrics

                # 🔹 Convert costs from micros to standard currency
                cost = metrics.cost_micros / 1e6
                cpc = metrics.average_cpc / 1e6 if metrics.average_cpc else 0
                sessions = metrics.interactions if metrics.interactions else 0
                cost_per_session = cost / sessions if sessions > 0 else 0
                conversions = metrics.conversions if metrics.conversions else 0
                cost_per_conversion = metrics.cost_per_conversion / 1e6 if metrics.cost_per_conversion else 0

                # ✅ Print campaign data
                print(f"📢 Campaign ID: {campaign.id}, Name: {campaign.name}")
                print(f"📊 Impressions: {metrics.impressions}, Clicks: {metrics.clicks}")
                print(f"💰 Cost: ${cost:.2f}, CPC: ${cpc:.2f}")
                print(f"🛠 Sessions: {sessions}, Cost per Session: ${cost_per_session:.2f}")
                print(f"🎯 Conversions: {conversions}, Cost per Conversion: ${cost_per_conversion:.2f}\n")

    except GoogleAdsException as ex:
        print(f"\n❌ Google Ads API Error: {ex}")
        for error in ex.failure.errors:
            print(f"Error message: {error.message}")
            if error.location:
                for field in error.location.field_path_elements:
                    print(f"Field: {field.field_name}")
        return None

# ✅ Replace with your test customer ID
TEST_CUSTOMER_ID = "4008564417"

# Run test
fetch_campaigns(TEST_CUSTOMER_ID)
