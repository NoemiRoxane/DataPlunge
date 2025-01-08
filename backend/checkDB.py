import sqlite3

def inspect_database(db_path):
    try:
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Alle Tabellen in der Datenbank anzeigen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tabellen in der Datenbank:")
        for table in tables:
            print(f"- {table[0]}")

        # Inhalte jeder Tabelle anzeigen
        for table in tables:
            table_name = table[0]
            print(f"\nInhalte der Tabelle: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Spalten:")
            for column in columns:
                print(f"  - {column[1]} ({column[2]})")

            # Daten aus der Tabelle anzeigen
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
            rows = cursor.fetchall()
            if rows:
                print("Beispieldaten:")
                for row in rows:
                    print(row)
            else:
                print("Keine Daten vorhanden.")

        # Verbindung schließen
        conn.close()
    except sqlite3.Error as e:
        print(f"Fehler beim Zugriff auf die Datenbank: {e}")

# Pfad zur SQLite-Datenbank angeben
db_path = "performance.db"  # Passe den Pfad an deine Datenbankdatei an
inspect_database(db_path)
