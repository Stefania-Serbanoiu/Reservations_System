from db import db_session


def insert_resource(name: str, type_: str, capacity: int):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO resources(name, type, capacity) VALUES (?, ?, ?)",
            (name, type_, capacity)
        )
        row = conn.execute(
            "SELECT id, name, type, capacity FROM resources WHERE id = ?",
            (cur.lastrowid,)
        ).fetchone()
        return dict(row)


def select_resources(type_=None, min_capacity=None, max_capacity=None):
    q = "SELECT id, name, type, capacity FROM resources WHERE 1=1"
    params = []
    if type_:
        q += " AND type = ?"
        params.append(type_)
    if min_capacity is not None:
        q += " AND capacity >= ?"
        params.append(min_capacity)
    if max_capacity is not None:
        q += " AND capacity <= ?"
        params.append(max_capacity)
    q += " ORDER BY capacity DESC, name ASC"

    with db_session() as conn:
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]


def find_resource_by_id(resource_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, name, type, capacity FROM resources WHERE id = ?",
            (resource_id,)
        ).fetchone()
        return dict(row) if row else None


def select_rooms(min_capacity=None):
    q = "SELECT id, name, type, capacity FROM resources WHERE type='room'"
    params = []
    if min_capacity is not None:
        q += " AND capacity >= ?"
        params.append(min_capacity)
    q += " ORDER BY capacity DESC, name ASC"
    with db_session() as conn:
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]