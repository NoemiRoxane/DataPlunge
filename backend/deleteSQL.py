import sqlite3

conn = sqlite3.connect('performance.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM performance')  # Alle Daten löschen
conn.commit()
conn.close()
