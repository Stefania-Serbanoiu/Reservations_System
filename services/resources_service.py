from fastapi import HTTPException
from models import ResourceCreate
from repos.users_repo import find_user_by_id
from repos.resources_repo import insert_resource, select_resources


def create_resource_admin(payload: ResourceCreate, admin_user_id: int):
    admin = find_user_by_id(admin_user_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    if int(admin["is_admin"]) != 1:
        raise HTTPException(status_code=403, detail="Not an admin")
    return insert_resource(payload.name, payload.type, payload.capacity)


def list_resources(type, min_capacity, max_capacity):
    return select_resources(type, min_capacity, max_capacity)
