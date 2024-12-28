import sqlite3

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('performance.db')
cursor = conn.cursor()

# Tabelle 'monthly_performance' neu erstellen
print("Überprüfe und erstelle die Tabelle 'monthly_performance'...")
cursor.execute('''
    DROP TABLE IF EXISTS monthly_performance
''')

cursor.execute('''
    CREATE TABLE monthly_performance (
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

print("Tabelle 'monthly_performance' erfolgreich erstellt.")

# Monatsweise Aggregation
print("Berechne monatliche Werte...")
cursor.execute('''
    INSERT INTO monthly_performance (month, costs, conversions, impressions, clicks, sessions, cost_per_click, cost_per_conversion)
    SELECT 
        strftime('%Y-%m', date) AS month,
        SUM(costs) AS total_costs,
        SUM(conversions) AS total_conversions,
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks,
        SUM(sessions) AS total_sessions,
        CASE WHEN SUM(clicks) > 0 THEN SUM(costs) / SUM(clicks) ELSE 0 END AS cost_per_click,
        CASE WHEN SUM(conversions) > 0 THEN SUM(costs) / SUM(conversions) ELSE 0 END AS cost_per_conversion
    FROM performance
    GROUP BY month
    ORDER BY month;
''')

# Ergebnisse überprüfen
conn.commit()
print("Monatliche Daten erfolgreich berechnet und gespeichert.")

cursor.execute("SELECT * FROM monthly_performance")
rows = cursor.fetchall()
print("\nDaten in 'monthly_performance':")
for row in rows:
    print(row)

# Verbindung schließen
conn.close()
