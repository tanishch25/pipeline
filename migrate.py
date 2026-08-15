import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE leads ADD COLUMN last_contacted_at DATETIME")
        cursor.execute("ALTER TABLE leads ADD COLUMN follow_up_count INTEGER DEFAULT 0")
        conn.commit()
        print("Database migrated successfully.")
    except Exception as e:
        print(f"Migration error (might already be migrated): {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
