import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).with_name("reservations.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_session():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                is_admin INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,               
                capacity INTEGER NOT NULL CHECK (capacity > 0)
            );

            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,           
                end_date TEXT NOT NULL,            
                status TEXT NOT NULL DEFAULT 'ACTIVE',  
                created_at TEXT NOT NULL DEFAULT (date('now')),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(resource_id) REFERENCES resources(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_res_resource_time
                ON reservations(resource_id, start_date, end_date);

            CREATE INDEX IF NOT EXISTS idx_res_user
                ON reservations(user_id);
            """
        )
