import sqlite3
import os
import json

DB_PATH = os.path.join("data", "cache.db")

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            links TEXT,
            crawled_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_cached_page(url):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT title, content, links FROM pages WHERE url = ?", (url,)
    ).fetchone()
    conn.close()
    if row:
        return {"title": row[0], "content": row[1], "links": json.loads(row[2]) if row[2] else []}
    return None

def save_page(url, title, content, links=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO pages (url, title, content, links) VALUES (?, ?, ?, ?)",
        (url, title, content, json.dumps(links or [])),
    )
    conn.commit()
    conn.close()