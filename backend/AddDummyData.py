import sqlite3

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect('performance.db')
cursor = conn.cursor()

# Dummy-Daten definieren
dummy_data = [
    ('2024-01-01', 500.0, 25, 20.0, 8000, 100, 200, 5.0, "Google Ads"),
    ('2024-01-15', 750.5, 30, 25.0, 9000, 150, 250, 5.5, "Microsoft Advertising"),
    ('2024-06-20', 1300.3, 60, 21.67, 15000, 300, 400, 4.3, "Google Ads"),
    ('2024-09-05', 900.7, 45, 20.01, 12000, 200, 300, 4.5, "Microsoft Advertising"),
    ('2024-10-10', 1500.7, 70, 21.43, 20000, 500, 800, 3.0, "Google Ads"),
    ('2024-10-15', 1700.2, 80, 21.25, 22000, 550, 850, 3.09, "Microsoft Advertising"),
    ('2024-11-21', 1000.5, 50, 20.01, 10000, 200, 300, 5.0, "Google Ads"),
    ('2024-11-22', 1200.75, 55, 21.82, 12000, 250, 400, 4.8, "Microsoft Advertising"),
    ('2024-12-01', 800.5, 40, 20.01, 9000, 180, 350, 4.45, "Google Ads"),
    ('2024-12-10', 1500.7, 70, 21.43, 18000, 450, 700, 3.33, "Microsoft Advertising"),
    ('2024-12-30', 2000.75, 90, 22.23, 25000, 600, 1000, 3.34, "Google Ads")
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
