import sqlite3

# Connect to the database
conn = sqlite3.connect('performance.db')
cursor = conn.cursor()

# Fetch table information
cursor.execute("PRAGMA table_info(performance);")
columns = cursor.fetchall()

print("Table schema for 'performance':")
for col in columns:
    print(f"Column ID: {col[0]}, Name: {col[1]}, Type: {col[2]}")

# Close the connection
conn.close()
