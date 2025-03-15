import sqlite3

def read_db(db_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_name in tables:
        print(f"\nTable: {table_name[0]}")
        cursor.execute(f"PRAGMA table_info({table_name[0]})")
        columns = cursor.fetchall()
        for column in columns:
            print(f"Column: {column[1]} - Type: {column[2]}")
        
        cursor.execute(f"SELECT * FROM {table_name[0]}")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    
    connection.close()

if __name__ == "__main__":
    db_path = "telebotumSql.db"  # Veritabanı dosyasının yolu
    read_db(db_path)