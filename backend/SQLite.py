import sqlite3

def check_database_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    
    # Query to retrieve all rows from the 'performance' table
    cursor.execute("SELECT * FROM performance;")
    rows = cursor.fetchall()
    
    # Print each row
    print("Data in 'performance' table:")
    for row in rows:
        print(row)
    
    # Close the connection to the database
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_database_data()
