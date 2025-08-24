from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    """Schema for user data in database."""
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    is_superuser: bool = False

    class Config:
        from_attributes = True

class User(UserInDB):
    """Schema for user response."""
    pass 