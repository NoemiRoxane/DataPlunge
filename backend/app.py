from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime


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
    

# Route to get filtered performance data
@app.route('/filter-performance', methods=['GET'])
def filter_performance():
    time_range = request.args.get('range')
    value = request.args.get('value')
    print(f"Received value from frontend: {value}")  # Debugging
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # Überprüfe alle verfügbaren Daten
    cursor.execute("SELECT DISTINCT date FROM performance;")
    print("All available dates in DB:", cursor.fetchall())

    if time_range == 'day':
        print(f"Filtering by day: {value}")
        query = """
            SELECT date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source
            FROM performance
            WHERE DATE(date) = DATE(?)
        """
        cursor.execute(query, (value,))
    elif time_range == 'range':
        start_date, end_date = value.split('|')
        print(f"Filtering by range from {start_date} to {end_date}")
        query = """
            SELECT date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source
            FROM performance
            WHERE DATE(date) BETWEEN DATE(?) AND DATE(?)
        """
        cursor.execute(query, (start_date, end_date))
    else:
        print("Invalid time range.")
        conn.close()
        return jsonify({'error': 'Invalid time range'}), 400

    rows = cursor.fetchall()
    print(f"Rows fetched for {value}: {rows}")
    conn.close()

    if not rows:
        print("No data found for the given range.")
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
    print(f"Filtered data returned: {filtered_data}")
    return jsonify(filtered_data)


# Route to get all performance data
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

@app.route('/insights', methods=['GET'])
def get_insights():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # Überprüfen Sie, ob Start- und Enddatum angegeben wurden
    if start_date and end_date:
        query = '''
            SELECT date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click
            FROM performance
            WHERE DATE(date) BETWEEN DATE(?) AND DATE(?)
            ORDER BY DATE(date)
        '''
        cursor.execute(query, (start_date, end_date))
    else:
        return jsonify({'error': 'Start date and end date must be provided'}), 400

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({'error': 'No data available for the given dates'}), 404

    insights = []
    total_costs = sum(row[1] for row in rows)
    total_conversions = sum(row[2] for row in rows)
    average_cost_per_conversion = total_costs / total_conversions if total_conversions > 0 else 0

    # Höchste Kosten
    highest_cost = max(rows, key=lambda x: x[1])
    insights.append({
        'date': highest_cost[0],
        'message': f'Highest costs were on {highest_cost[0]} with CHF {highest_cost[1]:.2f}.'
    })

    # Wachstumsberechnung
    if len(rows) > 1:
        prev_day = rows[0]
        for current_day in rows[1:]:
            growth_rate = ((current_day[1] - prev_day[1]) / prev_day[1] * 100) if prev_day[1] else 0
            insights.append({
                'date': current_day[0],
                'message': f'Costs grew by {growth_rate:.2f}% on {current_day[0]} compared to {prev_day[0]}.'
            })
            prev_day = current_day

    # Durchschnittliche Kosten pro Conversion
    insights.append({
        'message': f'Average cost per conversion for the period: CHF {average_cost_per_conversion:.2f}.'
    })

    return jsonify(insights)



if __name__ == '__main__':
    init_db()
    calculate_monthly_performance()
    app.run(debug=True)
