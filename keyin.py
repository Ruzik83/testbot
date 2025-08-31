import sqlite3

conn = sqlite3.connect("bot.db")
cur = conn.cursor()
try:
    cur.execute("ALTER TABLE tests ADD COLUMN created_at TEXT DEFAULT (datetime('now'))")
    print("✅ 'created_at' ustuni qo‘shildi.")
except Exception as e:
    print(f"ℹ️ Ustun qo‘shishda xatolik: {e}")
conn.commit()
conn.close()
