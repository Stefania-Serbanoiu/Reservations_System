from pydantic import BaseModel, Field
from typing import Optional, Literal

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    is_admin: bool = False

class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

class ResourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    type: Literal["room"] = "room"
    capacity: int = Field(gt=0, le=10000)

class ResourceOut(BaseModel):
    id: int
    name: str
    type: str
    capacity: int

class ReservationCreate(BaseModel):
    user_id: int
    resource_id: int
    start_date: str   
    end_date: str    

class ReservationOut(BaseModel):
    id: int
    user_id: int
    resource_id: int
    start_date: str
    end_date: str
    status: str
    created_at: str
