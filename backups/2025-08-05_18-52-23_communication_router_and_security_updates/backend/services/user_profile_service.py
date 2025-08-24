from sqlalchemy.orm import Session
from backend.models.user import User, UserProfile
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UserProfileService:
    """Service for managing user profiles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID"""
        try:
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            return profile
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> UserProfile:
        """Update user profile"""
        try:
            profile = self.get_user_profile(user_id)
            
            if not profile:
                # Create new profile
                profile = UserProfile(user_id=user_id)
                self.db.add(profile)
            
            # Update fields
            for key, value in data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            # Update completion percentage
            profile.profile_completion_percentage = self._calculate_completion(profile)
            
            self.db.commit()
            return profile
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise
    
    def get_profile_completion(self, user_id: str) -> int:
        """Get profile completion percentage"""
        try:
            profile = self.get_user_profile(user_id)
            
            if not profile:
                return 0
            
            return profile.profile_completion_percentage or 0
            
        except Exception as e:
            logger.error(f"Error getting profile completion: {e}")
            return 0
    
    def _calculate_completion(self, profile: UserProfile) -> int:
        """Calculate profile completion percentage"""
        required_fields = [
            'first_name', 'last_name', 'zip_code', 'dependents_count',
            'industry', 'job_title', 'employment_status'
        ]
        
        completed_fields = 0
        total_fields = len(required_fields)
        
        for field in required_fields:
            value = getattr(profile, field, None)
            if value and str(value).strip():
                completed_fields += 1
        
        return int((completed_fields / total_fields) * 100)
