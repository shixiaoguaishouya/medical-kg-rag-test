"""
从 SQLite 数据库读取医学选择题
"""
import sqlite3
from config import DB_PATH


def get_connection():
    """获取 SQLite 数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def read_one_question(question_id=None):
    """
    读取一道题目

    参数：
        question_id : int | None
            题目 ID；若为 None 则随机取一条

    返回：
        dict 或 None
    """
    conn = get_connection()
    cur = conn.cursor()

    if question_id is not None:
        cur.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
    else:
        cur.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")

    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def read_all_questions():
    """
    读取全部题目（供后续版本使用）

    返回：
        list[dict]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def count_questions():
    """返回题库总题数"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    count = cur.fetchone()[0]
    conn.close()
    return count
