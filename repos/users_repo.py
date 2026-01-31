from db import db_session


def insert_user(username: str, is_admin: bool):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO users(username, is_admin) VALUES (?, ?)",
            (username, 1 if is_admin else 0)
        )
        row = conn.execute(
            "SELECT id, username, is_admin FROM users WHERE id = ?",
            (cur.lastrowid,)
        ).fetchone()
        return dict(row)


def find_user_by_username(username: str):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, username, is_admin FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        return dict(row) if row else None
    

def find_user_all():
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, username, is_admin FROM users",
        ).fetchall()
        return [dict(r) for r in row]


def find_user_by_id(user_id: int): # for admin checks
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, username, is_admin FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
