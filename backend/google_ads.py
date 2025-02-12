from google.ads.googleads.client import GoogleAdsClient



# Path to your google-ads.yaml file
CONFIG_FILE_PATH = "google-ads.yaml"  # Ensure this is the correct path

# Initialize Google Ads client
client = GoogleAdsClient.load_from_storage(CONFIG_FILE_PATH)

# Replace with your Google Ads Customer ID
CUSTOMER_ID = "4008564417"

# Function to fetch campaign performance metrics
def get_campaign_performance(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")

    # Query to retrieve performance metrics
    query = """
        SELECT
            campaign.id,
            campaign.name,
            metrics.cost_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.average_cpc,
            metrics.sessions,
            metrics.conversions,
            metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY campaign.id
    """

    response = ga_service.search(customer_id=customer_id, query=query)

    # Print campaign performance details
    print("\n=== Google Ads Campaign Performance ===")
    for row in response:
        campaign = row.campaign
        metrics = row.metrics

        cost = metrics.cost_micros / 1_000_000  # Convert from micros to standard currency
        impressions = metrics.impressions
        clicks = metrics.clicks
        avg_cpc = metrics.average_cpc / 1_000_000 if metrics.average_cpc else 0
        sessions = metrics.sessions if hasattr(metrics, "sessions") else 0
        conversions = metrics.conversions
        cost_per_conversion = metrics.cost_per_conversion / 1_000_000 if metrics.cost_per_conversion else 0

        print(f"ID: {campaign.id}, Name: {campaign.name}")
        print(f"Costs: ${cost:.2f}, Impressions: {impressions}, Clicks: {clicks}")
        print(f"Avg CPC: ${avg_cpc:.2f}, Sessions: {sessions}, Conversions: {conversions}")
        print(f"Cost per Conversion: ${cost_per_conversion:.2f}\n")

# Run function
if __name__ == "__main__":
    get_campaign_performance(client, CUSTOMER_ID)
