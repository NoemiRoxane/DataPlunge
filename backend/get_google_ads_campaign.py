#!/usr/bin/env python
import argparse
import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# ✅ Path to Google Ads credentials
yaml_path = "C:\\Users\\Noemi\\DataPlunge\\google-ads.yaml"

# ✅ Load Google Ads API client
client = GoogleAdsClient.load_from_storage(yaml_path)

def fetch_campaign_performance(client, login_customer_id, customer_id):
    """Fetch and display Google Ads campaign performance metrics."""
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
        ORDER BY campaign.id
    """

    # ✅ Include MCC (login_customer_id) in the request
    stream = ga_service.search_stream(
        customer_id=customer_id,
        query=query,
        metadata=(("login-customer-id", login_customer_id),),  # ✅ Ensure MCC ID is used
    )

    print("\n=== Google Ads Campaign Performance ===")
    for batch in stream:
        for row in batch.results:
            campaign = row.campaign
            metrics = row.metrics

            cost = metrics.cost_micros / 1e6  # Convert from micros to dollars
            cpc = cost / metrics.clicks if metrics.clicks > 0 else 0
            cp_conversion = cost / metrics.conversions if metrics.conversions > 0 else 0

            print(f"Campaign ID: {campaign.id}, Name: {campaign.name}")
            print(f"Costs: ${cost:.2f}, Impressions: {metrics.impressions}, Clicks: {metrics.clicks}")
            print(f"Avg CPC: ${cpc:.2f}, Conversions: {metrics.conversions}, Cost per Conversion: ${cp_conversion:.2f}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Google Ads campaign performance metrics.")
    parser.add_argument("-c", "--customer_id", type=str, required=True, help="The Google Ads client customer ID.")

    args = parser.parse_args()

    try:
        # ✅ Get login_customer_id from `google-ads.yaml` (MCC ID)
        login_customer_id = client.login_customer_id
        if not login_customer_id:
            raise ValueError("Error: login_customer_id is not set in google-ads.yaml")

        fetch_campaign_performance(client, login_customer_id, args.customer_id)

    except GoogleAdsException as ex:
        print(f'Request failed with ID "{ex.request_id}" and status "{ex.error.code().name}"')
        for error in ex.failure.errors:
            print(f'Error: "{error.message}"')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"Field: {field_path_element.field_name}")
        sys.exit(1)
