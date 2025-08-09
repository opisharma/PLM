import mysql.connector

def connect_db():
    try:
        db = mysql.connector.connect(
            host="localhost",     
            user="root",          
            password="",          
            database="life_manger"  
        )
        print("✅ Connected to MySQL database successfully!")
        return db
    except mysql.connector.Error as err:
        print("❌ Failed to connect:", err)
        return None

if __name__ == "__main__":
    connection = connect_db()
    if connection:
        connection.close()
