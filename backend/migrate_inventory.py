
import sqlite3
import os

DB_PATH = "c:/Lanch/database/lanch.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(produtos)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "controlar_estoque" not in columns:
            print("Adding controlar_estoque column...")
            cursor.execute("ALTER TABLE produtos ADD COLUMN controlar_estoque BOOLEAN DEFAULT 0")
        
        if "estoque_atual" not in columns:
            print("Adding estoque_atual column...")
            cursor.execute("ALTER TABLE produtos ADD COLUMN estoque_atual INTEGER DEFAULT 0")
            
        conn.commit()
        print("Migration successful!")
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
