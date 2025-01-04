import sqlite3

def check_date_column():
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # Typ und Werte der 'date'-Spalte prüfen
    cursor.execute("SELECT typeof(date), date FROM performance;")
    results = cursor.fetchall()

    print("Type and Values of 'date' Column in 'performance' Table:")
    for row in results:
        print(f"Type: {row[0]}, Value: {row[1]}")

    conn.close()

def filter_by_date(date_to_filter):
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # Überprüfen, ob das Datum korrekt verarbeitet wird
    print(f"Filtering by day: {date_to_filter}")
    query = """
        SELECT date, costs, conversions, cost_per_conversion, impressions, clicks, sessions, cost_per_click, source
        FROM performance
        WHERE DATE(date) = DATE(?)
    """
    cursor.execute(query, (date_to_filter,))
    rows = cursor.fetchall()
    print(f"Rows fetched for {date_to_filter}: {rows}")

    if not rows:
        print("No data found for the given range.")

    conn.close()

def ensure_date_column_format():
    # Verbindung zur SQLite-Datenbank herstellen
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # Prüfen, ob die Spalte 'date' korrekt im ISO-8601-Format vorliegt
    print("Ensuring all dates are in ISO-8601 format...")
    cursor.execute("SELECT DISTINCT date FROM performance;")
    dates = cursor.fetchall()

    incorrect_dates = []
    for (date,) in dates:
        try:
            # Versuchen, das Datum in ein ISO-8601-Datum zu konvertieren
            sqlite3.datetime.date.fromisoformat(date)
        except ValueError:
            incorrect_dates.append(date)

    if incorrect_dates:
        print("Incorrectly formatted dates found:", incorrect_dates)
        print("Consider fixing the data format.")
    else:
        print("All dates are correctly formatted.")

    conn.close()

if __name__ == "__main__":
    # Schritt 1: Typ und Werte der 'date'-Spalte prüfen
    check_date_column()

    # Schritt 2: Sicherstellen, dass die Spalte 'date' korrekt formatiert ist
    ensure_date_column_format()

    # Schritt 3: Nach einem bestimmten Datum filtern
    date_to_filter = '2025-01-01'
    filter_by_date(date_to_filter)
