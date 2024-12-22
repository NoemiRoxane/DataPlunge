from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # CORS für alle Routen aktivieren

# Datenbank erstellen und Dummy-Daten einfügen
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
    return jsonify({'message': 'API läuft!'})

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
