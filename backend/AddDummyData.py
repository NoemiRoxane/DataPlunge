import sqlite3

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('performance.db')
cursor = conn.cursor()

# Dummy-Daten definieren
dummy_data = [
    ('2025-01-01', 1200.75, 55, 21.82, 12000, 250, 400, 4.8, "Microsoft Advertising"),
    ('2025-01-01', 800.5, 40, 20.01, 9000, 180, 350, 4.45, "Google Ads"),
    ('2025-01-04', 1500.7, 70, 21.43, 18000, 450, 700, 3.33, "Microsoft Advertising"),
    ('2025-01-05', 2000.75, 90, 22.23, 25000, 600, 1000, 3.34, "Google Ads")
]

# Daten in die Tabelle `performance` einfügen
cursor.executemany('''
    INSERT INTO performance (date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', dummy_data)

# Änderungen speichern und Verbindung schließen
conn.commit()
conn.close()

print("Dummy-Daten erfolgreich eingefügt!")
