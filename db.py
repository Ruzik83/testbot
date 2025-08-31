# db.py
"""
Comprehensive SQLite-backed database for Telegram test bot.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# ----------------------------- Config -----------------------------
try:
    from config import DB_FILE, GROUP_MAX_USERS_DEFAULT
except Exception:
    DB_FILE = "bot.db"
    GROUP_MAX_USERS_DEFAULT = 20

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db")

# ----------------------------- Connection helpers -----------------------------
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_cursor(commit: bool = False):
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_query(query: str, params: tuple = (), fetchone: bool = False, fetchall: bool = False, commit: bool = False):
    with get_cursor(commit=commit) as cur:
        cur.execute(query, params)
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
    return None

# ----------------------------- Initialization -----------------------------
def init_db():
    queries = [
        """CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )""",
        """CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(test_id) REFERENCES tests(id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_type TEXT NOT NULL,
            url TEXT NOT NULL,
            max_users INTEGER,
            current_users INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            full_name TEXT,
            score INTEGER DEFAULT 0,
            group_type TEXT,
            link_id INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            total INTEGER,
            link_id INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )"""
    ]
    with get_cursor(commit=True) as cur:
        for q in queries:
            cur.execute(q)
    logger.info("DB initialized (or already exists). File=%s", DB_FILE)

# ----------------------------- Tests CRUD -----------------------------
def add_test(name: str) -> int:
    if not name or not str(name).strip():
        raise ValueError("Test name cannot be empty")
    with get_cursor(commit=True) as cur:
        cur.execute("INSERT INTO tests (name) VALUES (?)", (name.strip(),))
        return cur.lastrowid

def get_test(test_id: int) -> Optional[Dict[str, Any]]:
    row = execute_query("SELECT * FROM tests WHERE id=?", (test_id,), fetchone=True)
    return dict(row) if row else None

def list_tests() -> List[Dict[str, Any]]:
    rows = execute_query("SELECT id, name, created_at FROM tests ORDER BY id", fetchall=True) or []
    return [dict(r) for r in rows]

def delete_test(test_id: int):
    execute_query("DELETE FROM tests WHERE id=?", (test_id,), commit=True)

def rename_test(test_id: int, new_name: str):
    if not new_name or not new_name.strip():
        raise ValueError("New name cannot be empty")
    execute_query("UPDATE tests SET name=? WHERE id=?", (new_name.strip(), test_id), commit=True)

# ----------------------------- Questions CRUD -----------------------------
def add_question(test_id: int, question: str, option_a: Optional[str] = None, option_b: Optional[str] = None,
                 option_c: Optional[str] = None, option_d: Optional[str] = None, correct: Optional[str] = None) -> int:
    if not question or not question.strip():
        raise ValueError("Question text cannot be empty")
    if correct is not None:
        c = str(correct).strip().upper()
        if c not in ("A", "B", "C", "D"):
            raise ValueError("correct must be one of A/B/C/D or None")
        correct = c
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO questions (test_id, question, option_a, option_b, option_c, option_d, correct) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (test_id, question.strip(), option_a, option_b, option_c, option_d, correct)
        )
        return cur.lastrowid

def get_question(question_id: int) -> Optional[Dict[str, Any]]:
    row = execute_query("SELECT * FROM questions WHERE id=?", (question_id,), fetchone=True)
    return dict(row) if row else None

def get_questions(test_id: int) -> List[Dict[str, Any]]:
    rows = execute_query("SELECT * FROM questions WHERE test_id=? ORDER BY id", (test_id,), fetchall=True) or []
    return [dict(r) for r in rows]

def update_question(question_id: int, **fields):
    allowed = {"question", "option_a", "option_b", "option_c", "option_d", "correct"}
    updates = []
    params = []
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k == "correct" and v is not None:
            vv = str(v).strip().upper()
            if vv not in ("A", "B", "C", "D"):
                raise ValueError("correct must be A/B/C/D")
            v = vv
        updates.append(f"{k}=?")
        params.append(v)
    if not updates:
        return False
    params.append(question_id)
    execute_query(f"UPDATE questions SET {', '.join(updates)} WHERE id=?", tuple(params), commit=True)
    return True

def delete_question(question_id: int):
    execute_query("DELETE FROM questions WHERE id=?", (question_id,), commit=True)

def count_questions(test_id: int) -> int:
    row = execute_query("SELECT COUNT(*) AS cnt FROM questions WHERE test_id=?", (test_id,), fetchone=True)
    return int(row["cnt"]) if row else 0

# ----------------------------- Links / Groups -----------------------------
def add_link(group_type: str, url: str, max_users: Optional[int] = None) -> int:
    if not group_type or not url:
        raise ValueError("group_type and url required")
    maxu = int(max_users) if max_users is not None else GROUP_MAX_USERS_DEFAULT
    with get_cursor(commit=True) as cur:
        cur.execute("INSERT INTO links (group_type, url, max_users) VALUES (?, ?, ?)", (group_type.upper(), url, maxu))
        return cur.lastrowid

def delete_link(link_id: int):
    execute_query("DELETE FROM links WHERE id=?", (link_id,), commit=True)

def list_links(group_prefix: Optional[str] = None) -> List[Dict[str, Any]]:
    if group_prefix:
        rows = execute_query("SELECT * FROM links WHERE group_type LIKE ? ORDER BY id", (group_prefix + "%",), fetchall=True) or []
    else:
        rows = execute_query("SELECT * FROM links ORDER BY id", fetchall=True) or []
    return [dict(r) for r in rows]

def get_available_link(group_letter: str) -> Optional[Dict[str, Any]]:
    rows = list_links(group_letter)
    for r in rows:
        maxu = r["max_users"] if r["max_users"] is not None else GROUP_MAX_USERS_DEFAULT
        if r["current_users"] < maxu:
            return r
    return None

def increment_link_users(link_id: int):
    execute_query("UPDATE links SET current_users = current_users + 1 WHERE id=?", (link_id,), commit=True)

def create_group_if_needed(group_letter: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT group_type FROM links WHERE group_type LIKE ? ORDER BY id DESC", (group_letter + "%",))
    rows = cur.fetchall()
    if rows:
        last = rows[0]["group_type"]
        try:
            num = int(last[1:]) + 1
        except Exception:
            num = 1
    else:
        num = 1

    while True:
        new_name = f"{group_letter}{num}"
        cur.execute("SELECT id FROM links WHERE group_type=?", (new_name,))
        if cur.fetchone():
            num += 1
            continue
        url = f"https://t.me/{new_name}_group"
        cur.execute("INSERT INTO links (group_type, url, max_users, current_users) VALUES (?, ?, ?, 0)",
                    (new_name, url, GROUP_MAX_USERS_DEFAULT))
        conn.commit()
        cur.execute("SELECT * FROM links WHERE group_type=?", (new_name,))
        created = cur.fetchone()
        conn.close()
        return dict(created) if created else None

# ----------------------------- Users / Results -----------------------------
def add_user_if_not_exists(user_id: int, full_name: str = ""):
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE id=?", (user_id,))
        if not cur.fetchone():
            cur.execute("INSERT INTO users (id, full_name, score, group_type, link_id) VALUES (?, ?, 0, ?, ?)", (user_id, full_name, None, None))

def update_user_group_and_score(user_id: int, group_type: Optional[str] = None, score: Optional[int] = None, link_id: Optional[int] = None):
    updates = []
    params = []
    if group_type is not None:
        updates.append("group_type=?"); params.append(group_type)
    if score is not None:
        updates.append("score=?"); params.append(score)
    if link_id is not None:
        updates.append("link_id=?"); params.append(link_id)
    if updates:
        params.append(user_id)
        execute_query(f"UPDATE users SET {', '.join(updates)} WHERE id=?", tuple(params), commit=True)

def save_result(user_id: int, score: int, total: int = None, link_id: Optional[int] = None):
    execute_query("INSERT INTO results (user_id, score, total, link_id) VALUES (?, ?, ?, ?)", (user_id, score, total, link_id), commit=True)
    execute_query("UPDATE users SET score=? WHERE id=?", (score, user_id), commit=True)

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    row = execute_query("SELECT * FROM users WHERE id=?", (user_id,), fetchone=True)
    return dict(row) if row else None

def list_results() -> List[Dict[str, Any]]:
    rows = execute_query("SELECT * FROM results ORDER BY id DESC", fetchall=True) or []
    return [dict(r) for r in rows]

# ----------------------------- Utility / Admin helpers -----------------------------
def list_all_tests_with_counts() -> List[Dict[str, Any]]:
    rows = execute_query(
        "SELECT t.id, t.name, COUNT(q.id) as qcount FROM tests t LEFT JOIN questions q ON q.test_id=t.id GROUP BY t.id ORDER BY t.id",
        fetchall=True
    ) or []
    return [{"id": r["id"], "name": r["name"], "qcount": r["qcount"]} for r in rows]

def get_test_name(test_id: int) -> Optional[str]:
    row = execute_query("SELECT name FROM tests WHERE id=?", (test_id,), fetchone=True)
    return row["name"] if row else None

def export_test_to_dict(test_id: int) -> Optional[Dict[str, Any]]:
    t = get_test(test_id)
    if not t:
        return None
    qs = execute_query("SELECT * FROM questions WHERE test_id=? ORDER BY id", (test_id,), fetchall=True) or []
    questions = [dict(r) for r in qs]
    return {"test": t, "questions": questions}

def import_test_from_dict(data: Dict[str, Any], overwrite: bool = False) -> int:
    test = data.get("test")
    questions = data.get("questions", [])
    if not test or not test.get("name"):
        raise ValueError("Invalid test dict")
    if overwrite and test.get("id"):
        delete_test(int(test.get("id")))
    tid = add_test(test.get("name"))
    for q in questions:
        add_question(tid, q.get("question"), q.get("option_a"), q.get("option_b"), q.get("option_c"), q.get("option_d"), q.get("correct"))
    return tid

# ----------------------------- Migration helper -----------------------------
def migrate_add_created_at():
    try:
        execute_query("ALTER TABLE tests ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP", commit=True)
        print("✅ 'created_at' ustuni qo‘shildi.")
    except Exception as e:
        print(f"ℹ️ Ustun qo‘shishda xatolik: {e}")

# ----------------------------- Initialize DB on import -----------------------------
init_db()
migrate_add_created_at()
