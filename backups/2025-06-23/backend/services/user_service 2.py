from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from supabase import Client
from enum import Enum
from loguru import logger
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend.models.user import User, Base
import re

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
    """Service class for user authentication and management"""
    
    def __init__(self, session_factory):
        """Initialize UserService with a session factory"""
        self.SessionLocal = session_factory
    
    def _get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[a-zA-Z]', password):
            return False, "Password must contain at least one letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict with user data and success status, or None if authentication fails
        """
        try:
            if not self.validate_email(email):
                logger.warning(f"Invalid email format: {email}")
                return None
            
            session = self._get_session()
            try:
                # Find user by email
                user = session.query(User).filter(
                    User.email == email.lower(),
                    User.is_active == True
                ).first()
                
                if not user:
                    logger.warning(f"User not found or inactive: {email}")
                    return None
                
                # Verify password
                if not check_password_hash(user.password_hash, password):
                    logger.warning(f"Invalid password for user: {email}")
                    return None
                
                # Return user data
                user_data = user.to_dict()
                user_data['success'] = True
                
                logger.info(f"User authenticated successfully: {email}")
                return user_data
                
            finally:
                session.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during authentication: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        
        Args:
            email: User's email address
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            if not self.validate_email(email):
                logger.warning(f"Invalid email format: {email}")
                return None
            
            session = self._get_session()
            try:
                user = session.query(User).filter(
                    User.email == email.lower(),
                    User.is_active == True
                ).first()
                
                if user:
                    return user.to_dict()
                else:
                    return None
                    
            finally:
                session.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by email: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user by email: {str(e)}")
            return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create new user account
        
        Args:
            user_data: Dictionary containing user information
                - email: User's email address
                - password: User's password (will be hashed)
                - full_name: User's full name
                - phone_number: User's phone number (optional)
                
        Returns:
            Created user data dictionary or None if creation fails
        """
        try:
            email = user_data.get('email', '').strip().lower()
            password = user_data.get('password', '')
            full_name = user_data.get('full_name', '').strip()
            phone_number = user_data.get('phone_number', '').strip()
            
            # Validate required fields
            if not email or not password or not full_name:
                logger.error("Missing required fields for user creation")
                return None
            
            # Validate email format
            if not self.validate_email(email):
                logger.error(f"Invalid email format: {email}")
                return None
            
            # Validate password strength
            password_valid, password_message = self.validate_password_strength(password)
            if not password_valid:
                logger.error(f"Password validation failed: {password_message}")
                return None
            
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                logger.warning(f"User already exists: {email}")
                return None
            
            # Hash password
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            
            session = self._get_session()
            try:
                # Create new user
                new_user = User(
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    phone_number=phone_number,
                    is_active=True
                )
                
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                
                logger.info(f"User created successfully: {email}")
                return new_user.to_dict()
                
            except IntegrityError as e:
                session.rollback()
                logger.error(f"Integrity error creating user: {str(e)}")
                return None
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database error creating user: {str(e)}")
                return None
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Unexpected error creating user: {str(e)}")
            return None
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            update_data: Dictionary with fields to update
            
        Returns:
            Updated user data dictionary or None if update fails
        """
        session = self._get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return None
            
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(user)
            
            return user.to_dict()
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating user: {str(e)}")
            return None
        finally:
            session.close()
    
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate user account
        
        Args:
            user_id: User ID
            
        Returns:
            True if deactivation is successful, False otherwise
        """
        session = self._get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deactivating user: {str(e)}")
            return False
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User data dictionary or None if not found
        """
        session = self._get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                return user.to_dict()
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by id: {str(e)}")
            return None
        finally:
            session.close()

    def get_welcome_message(self, user_id: str) -> str:
        """
        Generate welcome message for user
        
        Args:
            user_id: User ID
            
        Returns:
            Welcome message string
        """
        user = self.get_user_by_id(user_id)
        if user and user.get('full_name'):
            return f"Welcome back, {user['full_name']}!"
        return "Welcome to Mingus!" 