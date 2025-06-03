from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str

class UserCreate(UserBase):
    password: str
    phone: Optional[str] = None
    designation: Optional[str] = None
    photo_url: Optional[str] = None

class UserCreateByAdmin(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    phone: Optional[str] = None
    designation: Optional[str] = None
    photo_url: Optional[str] = None
    territory: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[str] = None
    territory: Optional[str] = None

class User(UserBase):
    id: int
    phone: Optional[str] = None
    designation: Optional[str] = None
    photo_url: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    last_location_update: Optional[datetime] = None
    status: str
    territory: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Location schemas
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

# Lead schemas
class LeadBase(BaseModel):
    company_name: str
    contact_person: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    latitude: float
    longitude: float
    priority: str = "medium"
    estimated_value: Optional[float] = None
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class Lead(LeadBase):
    id: int
    status: str
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Assignment schemas
class AssignmentCreate(BaseModel):
    lead_id: int
    salesperson_id: int
    notes: Optional[str] = None

class Assignment(BaseModel):
    id: int
    lead_id: int
    salesperson_id: int
    assigned_by: Optional[int] = None
    assigned_at: datetime
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Salesperson with distance
class SalespersonWithDistance(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    email: str
    designation: Optional[str] = None
    photo_url: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    last_location_update: Optional[datetime] = None
    status: str
    distance_km: float

    class Config:
        from_attributes = True
