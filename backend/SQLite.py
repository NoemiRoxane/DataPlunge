import sqlite3

conn = sqlite3.connect('performance.db')
cursor = conn.cursor()

# Tabellen prüfen
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tabellen:", cursor.fetchall())

# Inhalte der Tabelle "performance" prüfen
cursor.execute("SELECT * FROM performance;")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
