import sqlite3

DB_FILE = "bot.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()
try:
    cur.execute("ALTER TABLE tests ADD COLUMN created_at TEXT DEFAULT (datetime('now'))")
    print("✅ 'created_at' ustuni qo‘shildi.")
except sqlite3.OperationalError as e:
    print(f"ℹ️ Ehtimol ustun allaqachon mavjud: {e}")
finally:
    conn.commit()
    conn.close()
