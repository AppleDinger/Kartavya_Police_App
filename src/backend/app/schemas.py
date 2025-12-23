from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    # NEW: Send photo on login
    profile_photo: str

class CheckInRequest(BaseModel):
    latitude: float
    longitude: float

class BulkDeployRequest(BaseModel):
    officer_ids: List[int]
    latitude: float
    longitude: float
    radius: float

class OfficerStatusResponse(BaseModel):
    id: int
    username: str
    current_lat: Optional[float]
    current_long: Optional[float]
    status_color: str
    last_update: Optional[datetime]
    leave_requested: bool
    # NEW: Included in status list
    profile_photo: str

    class Config:
        from_attributes = True