from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from supabase import Client
from enum import Enum
from loguru import logger

class IncomeRange(str, Enum):
    UNDER_25K = "under_25k"
    RANGE_25K_50K = "25k_50k"
    RANGE_50K_75K = "50k_75k"
    RANGE_75K_100K = "75k_100k"
    RANGE_100K_150K = "100k_150k"
    RANGE_150K_200K = "150k_200k"
    OVER_200K = "over_200k"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    phone: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1-555-555-5555"
            }
        }
    )

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserService:
    def __init__(self, supabase_client: Client):
        self.db = supabase_client
        self.table = "users"

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        try:
            # Check if user already exists
            existing = await self.db.table(self.table)\
                .select("*")\
                .eq("email", user_data.email)\
                .execute()

            if existing.data:
                raise ValueError("User with this email already exists")

            # Create auth user
            auth_user = await self.db.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password
            })

            if not auth_user.user:
                raise ValueError("Failed to create auth user")

            # Create user profile
            result = await self.db.table(self.table).insert({
                "id": auth_user.user.id,
                "email": user_data.email,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "phone": user_data.phone,
                "created_at": datetime.now().isoformat()
            }).execute()

            if not result.data:
                raise ValueError("Failed to create user profile")

            return UserResponse(**result.data[0])

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise e

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """Get a user by ID."""
        try:
            result = await self.db.table(self.table)\
                .select("*")\
                .eq("id", user_id)\
                .execute()

            if result.data:
                return UserResponse(**result.data[0])
            return None

        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise e

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get a user by email."""
        try:
            result = await self.db.table(self.table)\
                .select("*")\
                .eq("email", email)\
                .execute()

            if result.data:
                return UserResponse(**result.data[0])
            return None

        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise e

    async def update_user(self, user_id: str, user_data: dict) -> UserResponse:
        """Update a user's profile."""
        try:
            result = await self.db.table(self.table)\
                .update({
                    **user_data,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("id", user_id)\
                .execute()

            if not result.data:
                raise ValueError("Failed to update user")

            return UserResponse(**result.data[0])

        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise e

    async def delete_user(self, user_id: str) -> None:
        """Delete a user."""
        try:
            # Delete auth user
            await self.db.auth.admin.delete_user(user_id)

            # Delete user profile
            result = await self.db.table(self.table)\
                .delete()\
                .eq("id", user_id)\
                .execute()

            if not result.data:
                raise ValueError("Failed to delete user profile")

        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise e

    def get_welcome_message(self, user_id: str) -> str:
        """Get a personalized welcome message for a user."""
        try:
            # This is a placeholder - you can make this more sophisticated
            # by using the user's name, onboarding data, etc.
            return "Welcome to Mingus! Let's start your financial journey together."
        except Exception as e:
            logger.error(f"Error getting welcome message: {str(e)}")
            return "Welcome to Mingus!" 