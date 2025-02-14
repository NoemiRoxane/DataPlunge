from flask import Flask, redirect, request, session, jsonify
import requests
import os
from flask_cors import CORS
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime


app = Flask(__name__)


CORS(app)  # Enable CORS for all routes

DATABASE_URL = "dbname='dataplunge' user='user' host='localhost' password='admin'"

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()
 
# Route to get filtered performance data

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

if __name__ == '__main__':

    app.run(debug=True)
