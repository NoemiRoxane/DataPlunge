from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database and create tables
def init_db():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # Create the performance table with all columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            date TEXT,
            costs REAL,
            conversions INTEGER,
            cost_per_conversion REAL,
            impressions INTEGER,
            clicks INTEGER,
            sessions INTEGER,
            cost_per_click REAL,
            source TEXT UNIQUE
        )
    ''')

    # Create the monthly_performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_performance (
            month TEXT PRIMARY KEY,
            costs REAL,
            conversions INTEGER,
            impressions INTEGER,
            clicks INTEGER,
            sessions INTEGER,
            cost_per_click REAL,
            cost_per_conversion REAL
        )
    ''')

    # Insert dummy data into performance if empty
    cursor.execute('SELECT COUNT(*) FROM performance')
    data_count = cursor.fetchone()[0]

    if data_count == 0:
        dummy_data = [
            ('2024-11-21', 1000.50, 50, 20.01, 10000, 200, 300, 5.0, "Google Ads"),
            ('2024-11-22', 1200.75, 55, 21.82, 12000, 250, 400, 4.8, "Microsoft Advertising")
        ]
        cursor.executemany('''
            INSERT INTO performance (date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', dummy_data)
        conn.commit()

    conn.close()

# Calculate monthly performance data
def calculate_monthly_performance():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # Delete old data in monthly_performance table
    cursor.execute("DELETE FROM monthly_performance")

    # Insert new aggregated monthly data
    cursor.execute('''
        INSERT INTO monthly_performance (month, costs, conversions, impressions, clicks, sessions, cost_per_click, cost_per_conversion)
        SELECT
            strftime('%Y-%m', date) AS month,
            SUM(costs) AS costs,
            SUM(conversions) AS conversions,
            SUM(impressions) AS impressions,
            SUM(clicks) AS clicks,
            SUM(sessions) AS sessions,
            CASE WHEN SUM(clicks) > 0 THEN SUM(costs) / SUM(clicks) ELSE 0 END AS cost_per_click,
            CASE WHEN SUM(conversions) > 0 THEN SUM(costs) / SUM(conversions) ELSE 0 END AS cost_per_conversion
        FROM performance
        GROUP BY month
        ORDER BY month;
    ''')

    conn.commit()
    conn.close()

# Route to get aggregated performance data by source
@app.route('/aggregated-performance', methods=['GET'])
def get_aggregated_performance():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            source, 
            SUM(costs) AS total_costs, 
            SUM(impressions) AS total_impressions, 
            SUM(clicks) AS total_clicks, 
            SUM(sessions) AS total_sessions, 
            SUM(conversions) AS total_conversions,
            CASE WHEN SUM(clicks) > 0 THEN SUM(costs) / SUM(clicks) ELSE 0 END AS cost_per_click,
            CASE WHEN SUM(conversions) > 0 THEN SUM(costs) / SUM(conversions) ELSE 0 END AS cost_per_conversion
        FROM performance
        GROUP BY source
    ''')
    rows = cursor.fetchall()
    conn.close()

    aggregated_data = [
        {
            'source': row[0],
            'costs': row[1],
            'impressions': row[2],
            'clicks': row[3],
            'sessions': row[4],
            'conversions': row[5],
            'cost_per_click': row[6],
            'cost_per_conversion': row[7],
        }
        for row in rows
    ]
    return jsonify(aggregated_data)    

# Route to get filtered performance data
@app.route('/filter-performance', methods=['GET'])
def filter_performance():
    time_range = request.args.get('range')  # Optionen: day, month, year, range
    value = request.args.get('value')      # z.B. '2024-12-10' oder '2024-12-01|2024-12-10'
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    if time_range == 'day':
        query = """
            SELECT date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source
            FROM performance
            WHERE date = ?
        """
        cursor.execute(query, (value,))
    elif time_range == 'range':
        start_date, end_date = value.split('|')
        query = """
            SELECT date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source
            FROM performance
            WHERE date BETWEEN ? AND ?
        """
        cursor.execute(query, (start_date, end_date))
    elif time_range == 'month':
        query = """
            SELECT strftime('%Y-%m', date) AS month, SUM(costs) AS total_costs, SUM(conversions) AS total_conversions,
                   CASE WHEN SUM(conversions) > 0 THEN SUM(costs) / SUM(conversions) ELSE 0 END AS cost_per_conversion
            FROM performance
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY month
        """
        cursor.execute(query, (value,))
    elif time_range == 'year':
        query = """
            SELECT strftime('%Y', date) AS year, SUM(costs) AS total_costs, SUM(conversions) AS total_conversions,
                   CASE WHEN SUM(conversions) > 0 THEN SUM(costs) / SUM(conversions) ELSE 0 END AS cost_per_conversion
            FROM performance
            WHERE strftime('%Y', date) = ?
            GROUP BY year
        """
        cursor.execute(query, (value,))
    else:
        conn.close()
        return jsonify({'error': 'Invalid time range'}), 400

    rows = cursor.fetchall()
    conn.close()

    # Überprüfe, ob Daten vorhanden sind
    if not rows:
        return jsonify([])

    filtered_data = [
        {
            'date': row[0],
            'costs': row[1],
            'conversions': row[2],
            'cost_per_conversion': row[3],
            'impressions': row[4],
            'clicks': row[5],
            'sessions': row[6],
            'cost_per_click': row[7],
            'source': row[8],
        }
        for row in rows
    ]
    return jsonify(filtered_data)


# Route to get insights
@app.route('/insights', methods=['GET'])
def get_insights():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM performance')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({'error': 'No data available'}), 404

    data = [
        {
            'date': row[0],
            'costs': row[1],
            'conversions': row[2],
            'cost_per_conversion': row[3],
            'impressions': row[4],
            'clicks': row[5],
            'sessions': row[6],
            'cost_per_click': row[7]
        }
        for row in rows
    ]

    insights = []

    # Highest costs
    highest_cost = max(data, key=lambda x: x['costs'])
    insights.append(f"Highest costs were on {highest_cost['date']} with CHF {highest_cost['costs']:.2f}.")

    # Daily growth insights
    for i in range(1, len(data)):
        prev = data[i - 1]
        curr = data[i]
        growth_rate = ((curr['costs'] - prev['costs']) / prev['costs']) * 100
        insights.append(f"On {curr['date']}, daily cost growth was {growth_rate:.2f}% compared to the previous day.")

    # Average cost per conversion
    avg_cost_per_conversion = sum(row['cost_per_conversion'] for row in data) / len(data)
    insights.append(f"Average cost per conversion is CHF {avg_cost_per_conversion:.2f} across all days.")

    return jsonify(insights)

if __name__ == '__main__':
    init_db()
    calculate_monthly_performance()
    app.run(debug=True)
