from fastapi import APIRouter, Query
from typing import Optional, List
from models import ReservationCreate, ReservationOut
from services.reservations_service import (
    create_reservation,
    cancel_reservation,
    my_reservations,
    availability,
    occupancy_report
)


router = APIRouter()


# 4) Creează rezervare
@router.post("/reservations", response_model=ReservationOut)
def create_reservation_route(payload: ReservationCreate):
    return create_reservation(payload)


# 5) Anulează rezervare
@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_reservation_route(reservation_id: int, actor_user_id: int = Query(...)):
    return cancel_reservation(reservation_id, actor_user_id)


# 6) Vezi rezervările mele
@router.get("/users/{user_id}/reservations", response_model=List[ReservationOut])
def my_reservations_route(user_id: int, include_cancelled: bool = False):
    return my_reservations(user_id, include_cancelled)


# 7) Disponibilitate
@router.get("/availability")
def availability_route(start_date: str, end_date: str, min_capacity: Optional[int] = None):
    return availability(start_date, end_date, min_capacity)


# 8) Raport ocupare
@router.get("/reports/occupancy")
def occupancy_report_route(day: str = Query(..., description="YYYY-MM-DD")):
    return occupancy_report(day)
