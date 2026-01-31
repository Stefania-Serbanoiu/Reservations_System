from db import db_session


def insert_reservation(user_id: int, resource_id: int, start_date: str, end_date: str):
    with db_session() as conn:
        cur = conn.execute(
            """
            INSERT INTO reservations(user_id, resource_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, 'ACTIVE')
            """,
            (user_id, resource_id, start_date, end_date)
        )
        row = conn.execute(
            """
            SELECT id, user_id, resource_id, start_date, end_date, status, created_at
            FROM reservations WHERE id = ?
            """,
            (cur.lastrowid,)
        ).fetchone()
        return dict(row)


def get_reservation_by_id(reservation_id: int):
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, resource_id, start_date, end_date, status, created_at
            FROM reservations WHERE id = ?
            """,
            (reservation_id,)
        ).fetchone()
        return dict(row) if row else None


def cancel_reservation_by_id(reservation_id: int):
    with db_session() as conn:
        conn.execute(
            "UPDATE reservations SET status = 'CANCELLED' WHERE id = ?",
            (reservation_id,)
        )


def list_reservations_by_user(user_id: int, include_cancelled: bool):
    q = """
        SELECT id, user_id, resource_id, start_date, end_date, status, created_at
        FROM reservations
        WHERE user_id = ?
    """
    params = [user_id]
    if not include_cancelled:
        q += " AND status = 'ACTIVE'"
    q += " ORDER BY start_date ASC"

    with db_session() as conn:
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]


def list_active_reservations_for_resource(resource_id: int):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT start_date, end_date
            FROM reservations
            WHERE resource_id = ? AND status = 'ACTIVE'
            """,
            (resource_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def count_reserved_rooms_for_day(day: str) -> int:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT COUNT(DISTINCT resource_id) AS cnt
            FROM reservations
            WHERE status='ACTIVE'
              AND start_date <= ?
              AND end_date >= ?
            """,
            (day, day)
        ).fetchone()
        return int(rows["cnt"]) if rows else 0


def count_total_rooms() -> int:
    with db_session() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM resources WHERE type='room'"
        ).fetchone()
        return int(row["cnt"]) if row else 0
