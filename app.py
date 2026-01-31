from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from datetime import date
from db import init_db, db_session
from models import (
    UserCreate, UserOut,
    ResourceCreate, ResourceOut,
    ReservationCreate, ReservationOut
)


app = FastAPI(title="Room Reservations")


@app.on_event("startup")
def _startup():
    init_db()

def parse_date(d: str) -> date:
    try:
        # acceptă "YYYY-MM-DD"
        return date.fromisoformat(d)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {d}, expected YYYY-MM-DD")

def ensure_interval(start_date_str: str, end_date_str: str):
    s = parse_date(start_date_str)
    e = parse_date(end_date_str)
    if e < s:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

def overlaps_dates(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    """
    Intervalele sunt considerate INCLUSIVE:
    [start_date, end_date]

    Se suprapun dacă NU se întâmplă:
    a_end < b_start sau a_start > b_end
    """
    a_s = parse_date(a_start)
    a_e = parse_date(a_end)
    b_s = parse_date(b_start)
    b_e = parse_date(b_end)
    return not (a_e < b_s or a_s > b_e)


# 1) Creează user
@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate):
    with db_session() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users(username, is_admin) VALUES (?, ?)",
                (payload.username, 1 if payload.is_admin else 0)
            )
        except Exception:
            # UNIQUE username
            raise HTTPException(status_code=409, detail="Username already exists")
        row = conn.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


# (simplu) “login”: întoarce user după username
@app.get("/users/by-username/{username}", response_model=UserOut)
def get_user_by_username(username: str):
    with db_session() as conn:
        row = conn.execute("SELECT id, username, is_admin FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)


# 2) Adaugă resursă (admin)
@app.post("/resources", response_model=ResourceOut)
def create_resource(payload: ResourceCreate, admin_user_id: int = Query(..., description="User id (must be admin)")):
    with db_session() as conn:
        u = conn.execute("SELECT is_admin FROM users WHERE id = ?", (admin_user_id,)).fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="Admin user not found")
        if int(u["is_admin"]) != 1:
            raise HTTPException(status_code=403, detail="Not an admin")

        cur = conn.execute(
            "INSERT INTO resources(name, type, capacity) VALUES (?, ?, ?)",
            (payload.name, payload.type, payload.capacity)
        )
        row = conn.execute("SELECT id, name, type, capacity FROM resources WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


# 3) Listează resurse + filtrare
@app.get("/resources", response_model=List[ResourceOut])
def list_resources(
    type: Optional[str] = None,
    min_capacity: Optional[int] = None,
    max_capacity: Optional[int] = None
):
    q = "SELECT id, name, type, capacity FROM resources WHERE 1=1"
    params = []
    if type:
        q += " AND type = ?"
        params.append(type)
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

# helper: verifică dacă resursa e liberă în interval (doar rezervări ACTIVE)
def is_available(conn, resource_id: int, start_date: str, end_date: str) -> bool:
    rows = conn.execute(
        """
        SELECT start_date, end_date FROM reservations
        WHERE resource_id = ? AND status = 'ACTIVE'
        """,
        (resource_id,)
    ).fetchall()
    for r in rows:
        if overlaps_dates(start_date, end_date, r["start_date"], r["end_date"]):
            return False
    return True

# 4) Creează rezervare (interval de zile)
@app.post("/reservations", response_model=ReservationOut)
def create_reservation(payload: ReservationCreate):
    ensure_interval(payload.start_date, payload.end_date)
    with db_session() as conn:
        # validări existență
        u = conn.execute("SELECT id FROM users WHERE id = ?", (payload.user_id,)).fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        res = conn.execute("SELECT id FROM resources WHERE id = ?", (payload.resource_id,)).fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Resource not found")

        if not is_available(conn, payload.resource_id, payload.start_date, payload.end_date):
            raise HTTPException(status_code=409, detail="Resource not available in that date interval")

        cur = conn.execute(
            """
            INSERT INTO reservations(user_id, resource_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, 'ACTIVE')
            """,
            (payload.user_id, payload.resource_id, payload.start_date, payload.end_date)
        )
        row = conn.execute(
            """
            SELECT id, user_id, resource_id, start_date, end_date, status, created_at
            FROM reservations WHERE id = ?
            """,
            (cur.lastrowid,)
        ).fetchone()
        return dict(row)

# 5) Anulează rezervare (doar proprietarul sau admin)
@app.post("/reservations/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_reservation(reservation_id: int, actor_user_id: int = Query(...)):
    with db_session() as conn:
        actor = conn.execute("SELECT id, is_admin FROM users WHERE id = ?", (actor_user_id,)).fetchone()
        if not actor:
            raise HTTPException(status_code=404, detail="Actor user not found")

        r = conn.execute(
            "SELECT * FROM reservations WHERE id = ?",
            (reservation_id,)
        ).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Reservation not found")

        if r["status"] != "ACTIVE":
            raise HTTPException(status_code=409, detail="Reservation is not ACTIVE")

        if actor_user_id != r["user_id"] and int(actor["is_admin"]) != 1:
            raise HTTPException(status_code=403, detail="Not allowed")

        conn.execute(
            "UPDATE reservations SET status = 'CANCELLED' WHERE id = ?",
            (reservation_id,)
        )
        row = conn.execute(
            """
            SELECT id, user_id, resource_id, start_date, end_date, status, created_at
            FROM reservations WHERE id = ?
            """,
            (reservation_id,)
        ).fetchone()
        return dict(row)

# 6) Vezi rezervările mele
@app.get("/users/{user_id}/reservations", response_model=List[ReservationOut])
def my_reservations(user_id: int, include_cancelled: bool = False):
    with db_session() as conn:
        u = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        q = """
            SELECT id, user_id, resource_id, start_date, end_date, status, created_at
            FROM reservations
            WHERE user_id = ?
        """
        params = [user_id]
        if not include_cancelled:
            q += " AND status = 'ACTIVE'"
        q += " ORDER BY start_date ASC"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

# 7) Caută disponibilitate pe interval de zile
@app.get("/availability")
def availability(start_date: str, end_date: str, min_capacity: Optional[int] = None):
    ensure_interval(start_date, end_date)
    with db_session() as conn:
        q = "SELECT id, name, type, capacity FROM resources WHERE type='room'"
        params = []
        if min_capacity is not None:
            q += " AND capacity >= ?"
            params.append(min_capacity)
        resources = conn.execute(q, params).fetchall()
        available = []
        for res in resources:
            if is_available(conn, res["id"], start_date, end_date):
                available.append(dict(res))
        return {"start_date": start_date, "end_date": end_date, "available": available}

# 8) Raport grad de ocupare (pe zi)
@app.get("/reports/occupancy")
def occupancy_report(day: str = Query(..., description="YYYY-MM-DD")):
    d = parse_date(day)

    with db_session() as conn:
        rooms = conn.execute("SELECT id FROM resources WHERE type='room'").fetchall()
        room_ids = [r["id"] for r in rooms]
        if not room_ids:
            return {"day": day, "rooms": 0, "reserved_rooms": 0, "occupancy_ratio": 0.0}

        # numărăm câte săli sunt rezervate în acea zi (distinct)
        rows = conn.execute(
            """
            SELECT DISTINCT resource_id FROM reservations
            WHERE status='ACTIVE'
              AND start_date <= ?
              AND end_date >= ?
            """,
            (day, day)
        ).fetchall()
        reserved_rooms = len(rows)
        total_rooms = len(room_ids)
        ratio = reserved_rooms / total_rooms if total_rooms else 0.0

        return {
            "day": day,
            "rooms": total_rooms,
            "reserved_rooms": reserved_rooms,
            "occupancy_ratio": ratio
        }
