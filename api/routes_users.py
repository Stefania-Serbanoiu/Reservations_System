from typing import List
from fastapi import APIRouter
from models import UserCreate, UserOut
from services.users_service import create_user, get_user_all, get_user_by_username


router = APIRouter()


@router.post("", response_model=UserOut)
def create_user_route(payload: UserCreate):
    return create_user(payload)


@router.get("/by-username/{username}", response_model=UserOut)
def get_user_by_username_route(username: str):
    return get_user_by_username(username)


@router.get("/", response_model=List[UserOut])
def get_all_users():
    return get_user_all()