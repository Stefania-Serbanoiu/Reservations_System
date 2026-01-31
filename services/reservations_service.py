from fastapi import HTTPException
from datetime import date
from models import ReservationCreate
from repos.users_repo import find_user_by_id
from repos.resources_repo import find_resource_by_id, select_rooms
from repos.reservations_repo import (
    insert_reservation,
    get_reservation_by_id,
    cancel_reservation_by_id,
    list_reservations_by_user,
    list_active_reservations_for_resource,
    count_reserved_rooms_for_day,
    count_total_rooms
)


def parse_date(d: str) -> date:
    try:
        return date.fromisoformat(d)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {d}, expected YYYY-MM-DD")


def ensure_interval(start_date_str: str, end_date_str: str):
    s = parse_date(start_date_str)
    e = parse_date(end_date_str)
    if e < s:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")


def overlaps_dates(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    # Interval inclusiv: [start_date, end_date]
    a_s = parse_date(a_start)
    a_e = parse_date(a_end)
    b_s = parse_date(b_start)
    b_e = parse_date(b_end)
    return not (a_e < b_s or a_s > b_e)


def is_available(resource_id: int, start_date: str, end_date: str) -> bool:
    rows = list_active_reservations_for_resource(resource_id)
    for r in rows:
        if overlaps_dates(start_date, end_date, r["start_date"], r["end_date"]):
            return False
    return True


def create_reservation(payload: ReservationCreate):
    ensure_interval(payload.start_date, payload.end_date)

    user = find_user_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    room = find_resource_by_id(payload.resource_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room["type"] != "room":
        raise HTTPException(status_code=400, detail="Resource is not a room")

    if not is_available(payload.resource_id, payload.start_date, payload.end_date):
        raise HTTPException(status_code=409, detail="Room not available in that date interval")

    return insert_reservation(
        user_id=payload.user_id,
        resource_id=payload.resource_id,
        start_date=payload.start_date,
        end_date=payload.end_date
    )


def cancel_reservation(reservation_id: int, actor_user_id: int):
    actor = find_user_by_id(actor_user_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Actor user not found")

    r = get_reservation_by_id(reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if r["status"] != "ACTIVE":
        raise HTTPException(status_code=409, detail="Reservation is not ACTIVE")

    is_admin = int(actor["is_admin"]) == 1
    if actor_user_id != r["user_id"] and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    cancel_reservation_by_id(reservation_id)
    return get_reservation_by_id(reservation_id)


def my_reservations(user_id: int, include_cancelled: bool):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return list_reservations_by_user(user_id, include_cancelled)


def availability(start_date: str, end_date: str, min_capacity: int | None):
    ensure_interval(start_date, end_date)
    rooms = select_rooms(min_capacity=min_capacity)

    available = []
    for room in rooms:
        if is_available(room["id"], start_date, end_date):
            available.append(room)

    return {"start_date": start_date, "end_date": end_date, "available": available}


def occupancy_report(day: str):
    parse_date(day)  # validează formatul

    total_rooms = count_total_rooms()
    if total_rooms == 0:
        return {"day": day, "rooms": 0, "reserved_rooms": 0, "occupancy_ratio": 0.0}

    reserved_rooms = count_reserved_rooms_for_day(day)
    ratio = reserved_rooms / total_rooms if total_rooms else 0.0

    return {
        "day": day,
        "rooms": total_rooms,
        "reserved_rooms": reserved_rooms,
        "occupancy_ratio": ratio
    }
