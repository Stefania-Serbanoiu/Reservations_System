from fastapi import APIRouter, Query
from typing import Optional, List
from models import ResourceCreate, ResourceOut
from services.resources_service import create_resource_admin, list_resources


router = APIRouter()


@router.post("", response_model=ResourceOut)
def create_resource_route(
    payload: ResourceCreate,
    admin_user_id: int = Query(..., description="User id (must be admin)")
):
    return create_resource_admin(payload, admin_user_id)


@router.get("", response_model=List[ResourceOut])
def list_resources_route(
    type: Optional[str] = None,
    min_capacity: Optional[int] = None,
    max_capacity: Optional[int] = None
):
    return list_resources(type, min_capacity, max_capacity)
