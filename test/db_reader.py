"""
SQLite database reader
"""
import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def read_one_question(question_id=None):
    conn = get_connection()
    cur = conn.cursor()
    if question_id is not None:
        cur.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    else:
        cur.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def read_all_questions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def count_questions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    count = cur.fetchone()[0]
    conn.close()
    return count
