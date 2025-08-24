import os
import mysql.connector

DB_CONFIG = {
    "host": os.getenv("LM_DB_HOST", "localhost"),
    "user": os.getenv("LM_DB_USER", "root"),
    "password": os.getenv("LM_DB_PASSWORD", "1234"),
    "database": os.getenv("LM_DB_NAME", "life_manger"),  # set LM_DB_NAME=life_manager if needed
}

def connect_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"❌ Failed to connect: {err}")
        return None

if __name__ == "__main__":
    conn = connect_db()
    if conn:
        print("✅ Connected to MySQL database successfully!")
        conn.close()
