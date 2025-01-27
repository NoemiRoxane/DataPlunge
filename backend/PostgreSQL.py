import psycopg2
from psycopg2 import OperationalError

def create_connection():
    """Create a database connection to a PostgreSQL database."""
    conn = None
    try:
        # Use your actual database parameters here
        conn = psycopg2.connect(
            dbname="dataplunge",
            user="user",
            password="admin",
            host="localhost"
        )
        
        # Create a cursor object
        cur = conn.cursor()
        
        # Fetch the server version
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        
        print("Connected to the database successfully.")
        print("PostgreSQL version:", db_version)
        
        # Close the cursor and connection to clean up
        cur.close()
        conn.close()
        
    except OperationalError as e:
        print(f"The error '{e}' occurred")

create_connection()
