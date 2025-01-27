import argparse
import uuid
import random
import datetime

from google.ads.googleads.client import GoogleAdsClient

customer_id = '2160203145'



# Check if the YAML file is accessible
yaml_path = "C:\\Users\\Noemi\\DataPlunge\\google-ads.yaml"
try:
    with open(yaml_path, 'r') as file:
        print("google-ads.yaml is accessible.")
except IOError:
    print("google-ads.yaml not accessible or does not exist at", yaml_path)

client = GoogleAdsClient.load_from_storage(yaml_path)


import argparse
import uuid
import random
import datetime
import sqlite3  # Required for database operations

from google.ads.googleads.client import GoogleAdsClient

def simulate_campaign_metrics():
    """Generates simulated campaign metrics."""
    impressions = random.randint(1000, 10000)
    clicks = random.randint(100, impressions)
    sessions = random.randint(clicks, impressions)
    cost = round(random.uniform(100.0, 1000.0), 2)
    cost_per_click = round(cost / clicks, 2) if clicks > 0 else 0
    cost_per_conversion = round(cost / (0.1 * clicks), 2) if clicks > 0 else 0
    return {
        'impressions': impressions,
        'clicks': clicks,
        'sessions': sessions,
        'cost': cost,
        'cost_per_click': cost_per_click,
        'cost_per_conversion': cost_per_conversion,
        'source': 'Google Ads'
    }

def insert_into_db(connection, campaign_name, data):
    """Inserts simulated data into the database."""
    cursor = connection.cursor()
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO performance (date, campaign_name, cost_per_conversion, source, impressions, clicks, sessions, cost_per_click)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (today_date, campaign_name, data['cost_per_conversion'], data['source'], data['impressions'], data['clicks'], data['sessions'], data['cost_per_click']))
    connection.commit()

def main(client, customer_id):
    connection = sqlite3.connect('performance.db')
    campaign_name = f"Kampagne1"  # You can still use UUID or any method to generate unique or desired names

    # Simulate data
    simulated_metrics = simulate_campaign_metrics()
    print(f"Simulated Metrics for {campaign_name}: {simulated_metrics}")

    # Insert data into the database
    insert_into_db(connection, campaign_name, simulated_metrics)

    connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulates and inserts campaign data.")
    parser.add_argument("-c", "--customer_id", type=str, required=True, help="The Google Ads customer ID.")
    args = parser.parse_args()

    client = GoogleAdsClient.load_from_storage("C:\\Users\\Noemi\\DataPlunge\\google-ads.yaml", version="v17")
    main(client, args.customer_id)
