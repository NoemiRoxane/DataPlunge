#!/usr/bin/env python
import argparse
import sys
import sqlite3

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

customer_id = '2160203145'
yaml_path = "C:\\Users\\Noemi\\DataPlunge\\google-ads.yaml"

try:
    with open(yaml_path, 'r') as file:
        print("google-ads.yaml is accessible.")
except IOError:
    print("google-ads.yaml not accessible or does not exist at", yaml_path)

client = GoogleAdsClient.load_from_storage(yaml_path)
conn = sqlite3.connect('performance.db')
c = conn.cursor()

def insert_data(data):
    c.execute('''
        INSERT INTO performance (date, costs, impressions, clicks, cost_per_click, source, conversions, cost_per_conversion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()

def main(client, customer_id):
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
    stream = ga_service.search_stream(customer_id=customer_id, query=query)
    for batch in stream:
        for row in batch.results:
            cost = row.metrics.cost_micros / 1e6
            cpc = cost / row.metrics.clicks if row.metrics.clicks > 0 else 0
            cp_conversion = cost / row.metrics.conversions if row.metrics.conversions > 0 else 0
            data = (
                'today\'s date',  # Adjust the date accordingly
                cost,
                row.metrics.impressions,
                row.metrics.clicks,
                cpc,
                'Google Ads',
                row.metrics.conversions,
                cp_conversion
            )
            insert_data(data)
            print(f"Data for campaign {row.campaign.name} inserted into database.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lists all campaigns for specified customer."
    )
    parser.add_argument(
        "-c",
        "--customer_id",
        type=str,
        required=True,
        help="The Google Ads customer ID.",
    )
    args = parser.parse_args()

    try:
        main(client, args.customer_id)
    except GoogleAdsException as ex:
        print(
            f'Request with ID "{ex.request_id}" failed with status '
            f'"{ex.error.code().name}" and includes the following errors:'
        )
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"\t\tOn field: {field_path_element.field_name}")
        sys.exit(1)
    finally:
        conn.close()
