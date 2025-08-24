from sqlalchemy.orm import Session
from backend.models import User, UserProfile
from backend.services.user_profile_service import UserProfileService
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OnboardingService:
    """Service for managing user onboarding"""
    
    def __init__(self, db: Session):
        self.db = db
        self.profile_service = UserProfileService(db)
    
    def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's onboarding status"""
        try:
            profile = self.profile_service.get_user_profile(user_id)
            
            if not profile:
                return {
                    'current_step': 1,
                    'total_steps': 5,
                    'completed_steps': [],
                    'completion_percentage': 0,
                    'is_completed': False
                }
            
            completed_steps = []
            current_step = 1
            
            # Check which steps are completed
            if profile.first_name and profile.last_name:
                completed_steps.append(1)
                current_step = 2
            
            if profile.zip_code and profile.dependents_count is not None:
                completed_steps.append(2)
                current_step = 3
            
            if profile.industry and profile.job_title:
                completed_steps.append(3)
                current_step = 4
            
            if profile.employment_status:
                completed_steps.append(4)
                current_step = 5
            
            if profile.profile_completion_percentage >= 80:
                completed_steps.append(5)
                current_step = 6
            
            return {
                'current_step': current_step,
                'total_steps': 5,
                'completed_steps': completed_steps,
                'completion_percentage': profile.profile_completion_percentage or 0,
                'is_completed': current_step > 5
            }
            
        except Exception as e:
            logger.error(f"Error getting onboarding status: {e}")
            return {
                'current_step': 1,
                'total_steps': 5,
                'completed_steps': [],
                'completion_percentage': 0,
                'is_completed': False
            }
    
    def complete_step(self, user_id: str, step: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete an onboarding step"""
        try:
            # Update profile with step data
            self.profile_service.update_user_profile(user_id, data)
            
            # Get updated status
            status = self.get_onboarding_status(user_id)
            
            return {
                'step': step,
                'status': status,
                'message': f'Step {step} completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error completing step {step}: {e}")
            raise
    
    def complete_onboarding(self, user_id: str) -> Dict[str, Any]:
        """Complete the entire onboarding process"""
        try:
            profile = self.profile_service.get_user_profile(user_id)
            
            if not profile:
                raise ValueError("User profile not found")
            
            # Mark onboarding as completed
            profile.onboarding_completed = True
            self.db.commit()
            
            return {
                'success': True,
                'completion_percentage': profile.profile_completion_percentage,
                'message': 'Onboarding completed successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing onboarding: {e}")
            raise
