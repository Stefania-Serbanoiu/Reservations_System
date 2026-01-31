from fastapi import HTTPException
from models import UserCreate
from repos.users_repo import find_user_all, insert_user, find_user_by_username


def create_user(payload: UserCreate):
    try:
        return insert_user(payload.username, payload.is_admin)
    except Exception:
        raise HTTPException(status_code=409, detail="Username already exists")


def get_user_by_username(username: str):
    row = find_user_by_username(username)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


def get_user_all():
    rows = find_user_all()
    if not rows:
        raise HTTPException(status_code=404, detail="Users not found")
    return rows