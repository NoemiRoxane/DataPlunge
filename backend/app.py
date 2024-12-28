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

# Route to add a data source and fetch data
@app.route('/add-data-source', methods=['POST'])
def add_data_source():
    data = request.json
    source = data.get('source')
    if not source:
        return jsonify({'error': 'Missing source name'}), 400

    try:
        conn = sqlite3.connect('performance.db')
        cursor = conn.cursor()

        # Check if the source already exists
        cursor.execute('SELECT COUNT(*) FROM performance WHERE source = ?', (source,))
        exists = cursor.fetchone()[0]

        if exists:
            conn.close()
            return jsonify({'error': f'Source {source} already exists in the database.'}), 400

        # Fetch data from the corresponding API
        if source == "Google Ads":
            fetched_data = fetch_google_ads_data()
        elif source == "Microsoft Advertising":
            fetched_data = fetch_microsoft_ads_data()
        else:
            fetched_data = []

        # Insert fetched data into the performance table
        for record in fetched_data:
            cursor.execute('''
                INSERT INTO performance (date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (record['date'], record['costs'], record['conversions'], record['cost_per_conversion'],
                  record['impressions'], record['clicks'], record['sessions'], record['cost_per_click'], source))

        conn.commit()
        conn.close()

        # Recalculate monthly data after insert
        calculate_monthly_performance()

        return jsonify({'message': f'Successfully connected {source} and fetched data.'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': f'Source {source} already exists in the database.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
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

# Route to get performance data
@app.route('/performance', methods=['GET'])
def get_performance():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM performance')
    rows = cursor.fetchall()
    conn.close()

    performance_data = [
        {
            'date': row[0],
            'costs': row[1],
            'conversions': row[2],
            'cost_per_conversion': row[3],
            'impressions': row[4],
            'clicks': row[5],
            'sessions': row[6],
            'cost_per_click': row[7],
            'source': row[8]
        }
        for row in rows
    ]
    return jsonify(performance_data)

# Route to get monthly performance data
@app.route('/monthly-performance', methods=['GET'])
def get_monthly_performance():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monthly_performance")
    rows = cursor.fetchall()
    conn.close()

    monthly_data = [
        {
            'month': row[0],
            'costs': row[1],
            'conversions': row[2],
            'impressions': row[3],
            'clicks': row[4],
            'sessions': row[5],
            'cost_per_click': row[6],
            'cost_per_conversion': row[7],
        }
        for row in rows
    ]
    return jsonify(monthly_data)

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
