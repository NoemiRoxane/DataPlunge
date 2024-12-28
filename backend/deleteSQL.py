import sqlite3

def remove_duplicates_and_add_constraint():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()

    # 1. Backup erstellen (optional, aber empfohlen)
    print("Creating a backup of the performance table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_backup AS SELECT * FROM performance
    ''')

    # 2. Entferne doppelte Einträge aus der Tabelle
    print("Removing duplicate entries...")
    cursor.execute('''
        DELETE FROM performance
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM performance
            GROUP BY source
        )
    ''')

    # 3. UNIQUE-Constraint zur Spalte 'source' hinzufügen
    print("Adding UNIQUE constraint to the 'source' column...")
    try:
        cursor.execute('''
            ALTER TABLE performance ADD CONSTRAINT unique_source UNIQUE (source)
        ''')
    except sqlite3.OperationalError as e:
        print("Constraint could not be added:", e)

    # Optional: Überprüfen, ob die Tabelle jetzt korrekt ist
    print("Checking final table state...")
    cursor.execute('SELECT * FROM performance')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    conn.commit()
    conn.close()
    print("Completed.")

if __name__ == '__main__':
    remove_duplicates_and_add_constraint()
