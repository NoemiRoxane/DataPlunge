from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # CORS für alle Routen aktivieren

# Datenbank initialisieren und Dummy-Daten einfügen
def init_db():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance (
            date TEXT,
            costs REAL,
            conversions INTEGER,
            cost_per_conversion REAL
        )
    ''')
    # Überprüfen, ob die Tabelle bereits Daten enthält
    cursor.execute('SELECT COUNT(*) FROM performance')
    data_count = cursor.fetchone()[0]
    
    if data_count == 0:  # Nur Daten einfügen, wenn Tabelle leer ist
        data = [
            ('2024-11-21', 1000.50, 50, 20.01),
            ('2024-11-22', 1200.75, 55, 21.82),
            ('2024-11-23', 1500.10, 60, 25.00),
            ('2024-11-24', 1800.30, 65, 27.70),
            ('2024-11-25', 2000.90, 70, 28.58),
            ('2024-11-26', 2200.45, 75, 29.34),
            ('2024-11-27', 2500.00, 80, 31.25),
        ]
        cursor.executemany('''
            INSERT INTO performance (date, costs, conversions, cost_per_conversion)
            VALUES (?, ?, ?, ?)
        ''', data)
        conn.commit()
    
    conn.close()

@app.route('/')
def home():
    return jsonify({'message': 'API is running!'})

@app.route('/performance', methods=['GET'])
def get_performance():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM performance')
    rows = cursor.fetchall()
    conn.close()
    
    # Daten als JSON zurückgeben
    performance_data = [
        {'date': row[0], 'costs': row[1], 'conversions': row[2], 'cost_per_conversion': row[3]}
        for row in rows
    ]
    return jsonify(performance_data)

@app.route('/insights', methods=['GET'])
def get_insights():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM performance')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return jsonify({'error': 'No data available'}), 404

    data = [{'date': row[0], 'costs': row[1], 'conversions': row[2], 'cost_per_conversion': row[3]} for row in rows]

    insights = []

    # 1. Höchste Kosten
    highest_cost = max(data, key=lambda x: x['costs'])
    insights.append(f"Highest costs were on {highest_cost['date']} with CHF {highest_cost['costs']:.2f}.")

    # 2. Wachstumsberechnung
    growth_insights = []
    for i in range(1, len(data)):
        prev = data[i - 1]
        curr = data[i]
        growth_rate = ((curr['costs'] - prev['costs']) / prev['costs']) * 100
        growth_insights.append({'date': curr['date'], 'growth_rate': growth_rate})
    
    if growth_insights:
        highest_growth = max(growth_insights, key=lambda x: x['growth_rate'])
        insights.append(f"Highest daily cost growth was on {highest_growth['date']} with {highest_growth['growth_rate']:.2f}%.")

    # Wachstumsrate für alle Tage hinzufügen
    for growth in growth_insights:
        insights.append(f"On {growth['date']}, the daily cost growth was {growth['growth_rate']:.2f}% compared to the previous day.")

    # 3. Durchschnittliche Kosten pro Conversion
    avg_cost_per_conversion = sum(row['cost_per_conversion'] for row in data) / len(data)
    insights.append(f"Average cost per conversion is CHF {avg_cost_per_conversion:.2f} across all days.")

    return jsonify(insights)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
