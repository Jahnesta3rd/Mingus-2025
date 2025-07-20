from typing import Optional, Dict, Any
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend.models.user_profile import UserProfile
from backend.models.onboarding_progress import OnboardingProgress
from backend.models.financial_questionnaire_submission import FinancialQuestionnaireSubmission
import json
from backend.routes.financial_profile import validate_profile
from flask import current_app
from backend.analytics.business_intelligence import business_intelligence
import os
from flask_migrate import Migrate
from prometheus_client import make_wsgi_app

class OnboardingService:
    def __init__(self, session_factory):
        """Initialize OnboardingService with a session factory"""
        self.SessionLocal = session_factory

    def _get_session(self):
        """Get a new database session."""
        return self.SessionLocal()

    def create_user_profile(self, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates a new user profile record in the database.
        Validates required fields and ensures data integrity.
        """
        session = self._get_session()
        try:
            if 'user_id' not in profile_data or not profile_data['user_id']:
                raise ValueError("`user_id` is a required field.")

            new_profile = UserProfile(**profile_data)
            
            session.add(new_profile)
            session.commit()
            session.refresh(new_profile)

            logger.info(f"Successfully created user profile for user_id: {new_profile.user_id}")
            return new_profile.to_dict()

        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error creating user profile: {e}")
            return None
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error during user profile creation: {e}")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"An unexpected error occurred during profile creation: {e}")
            return None
        finally:
            session.close()

    def create_onboarding_record(self, onboarding_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates a new onboarding record for a user.
        """
        session = self._get_session()
        try:
            if 'user_id' not in onboarding_data or not onboarding_data['user_id']:
                raise ValueError("`user_id` is required to create an onboarding record.")

            new_onboarding_record = OnboardingProgress(**onboarding_data)

            session.add(new_onboarding_record)
            session.commit()
            session.refresh(new_onboarding_record)

            logger.info(f"Successfully created onboarding record for user_id: {new_onboarding_record.user_id}")
            return new_onboarding_record.to_dict()

        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error creating onboarding record: {e}")
            return None
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error during onboarding record creation: {e}")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"An unexpected error occurred during onboarding record creation: {e}")
            return None
        finally:
            session.close()

    def update_onboarding_progress(self, user_id: str, step_name: str, is_completed: bool = True, responses: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Updates the onboarding progress for a user.
        """
        session = self._get_session()
        try:
            onboarding_record = session.query(OnboardingProgress).filter_by(user_id=user_id).first()
            if not onboarding_record:
                logger.warning(f"No onboarding record found for user_id: {user_id} to update.")
                return None
            # Use model's update_progress for step tracking
            onboarding_record.update_progress(step_name, is_completed)
            if responses:
                if hasattr(onboarding_record, 'responses') and onboarding_record.responses:
                    onboarding_record.responses.update(responses)
                elif hasattr(onboarding_record, 'responses'):
                    onboarding_record.responses = responses
            # Validate financial profile and mark completion
            profile_valid = self.validate_financial_profile(user_id)['valid']
            if step_name == 'financial_profile' and profile_valid:
                onboarding_record.is_complete = True
                onboarding_record.completed_at = datetime.now(timezone.utc)
                self.trigger_welcome_email(user_id)
            session.commit()
            session.refresh(onboarding_record)
            logger.info(f"Successfully updated onboarding progress for user_id: {user_id} at step: {step_name}")
            return onboarding_record.to_dict()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating onboarding progress for user_id {user_id}: {e}")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"An unexpected error occurred while updating onboarding progress for user_id {user_id}: {e}")
            return None
        finally:
            session.close()

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user's profile from the database.
        """
        session = self._get_session()
        try:
            profile = session.query(UserProfile).filter_by(user_id=user_id).first()
            if profile:
                return profile.to_dict()
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user profile for user_id {user_id}: {e}")
            return None
        finally:
            session.close()

    def get_onboarding_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user's onboarding progress.
        """
        session = self._get_session()
        try:
            progress = session.query(OnboardingProgress).filter_by(user_id=user_id).first()
            if progress:
                return progress.to_dict()
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving onboarding progress for user_id {user_id}: {e}")
            return None
        finally:
            session.close()

    def get_onboarding_step_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns the step_status JSON for the user's onboarding progress (for React tracker).
        """
        session = self._get_session()
        try:
            progress = session.query(OnboardingProgress).filter_by(user_id=user_id).first()
            if progress and progress.step_status:
                return json.loads(progress.step_status)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving onboarding step status for user_id {user_id}: {e}")
            return None
        finally:
            session.close()

    def update_user_profile(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates an existing user profile with new data.
        """
        session = self._get_session()
        try:
            profile = session.query(UserProfile).filter_by(user_id=user_id).first()
            if not profile:
                logger.warning(f"No user profile found for user_id: {user_id} to update.")
                return None

            for key, value in update_data.items():
                setattr(profile, key, value)
            
            session.commit()
            session.refresh(profile)

            logger.info(f"Successfully updated user profile for user_id: {user_id}")
            return profile.to_dict()

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating user profile for user_id {user_id}: {e}")
            return None
        finally:
            session.close()

    def is_onboarding_complete(self, user_id: str) -> bool:
        """
        Checks if the user has completed the onboarding process.
        """
        progress = self.get_onboarding_progress(user_id)
        return progress.get('is_completed', False) if progress else False

    def validate_financial_profile(self, user_id: str) -> Dict[str, Any]:
        """Validate the user's financial profile and return errors/suggestions."""
        profile = self.get_user_profile(user_id)
        errors = validate_profile(profile or {})
        suggestions = self.generate_profile_suggestions(profile or {})
        return {'valid': not errors, 'errors': errors, 'suggestions': suggestions}

    def get_completion_percentage(self, user_id: str) -> int:
        """Calculate onboarding completion percentage based on required steps."""
        progress = self.get_onboarding_progress(user_id)
        if not progress:
            return 0
        total_steps = progress.get('total_steps', 5)
        completed_steps = progress.get('completed_steps', 0)
        return int((completed_steps / total_steps) * 100) if total_steps else 0

    def generate_profile_suggestions(self, profile: Dict[str, Any]) -> list:
        """Generate suggestions for missing or incomplete financial profile data."""
        suggestions = []
        if not profile.get('income') or profile['income'] <= 0:
            suggestions.append('Add your primary income to get started.')
        if not profile.get('expenses') or profile['expenses'] < 0:
            suggestions.append('Add your monthly expenses for accurate insights.')
        if not profile.get('emergency_fund') or profile['emergency_fund'] < (profile.get('expenses', 0) * 3):
            suggestions.append('Build an emergency fund of at least 3 months of expenses.')
        # Add more as needed
        return suggestions

    def trigger_welcome_email(self, user_id: str):
        """Trigger a welcome email when onboarding is complete."""
        # TODO: Integrate with email service
        logger.info(f"Triggering welcome email for user_id: {user_id}")

    def save_questionnaire_data(self, user_id: str, questionnaire_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Saves financial questionnaire data for a user.
        
        Args:
            user_id: User ID
            questionnaire_data: Questionnaire response data
            
        Returns:
            Saved questionnaire data or None if failed
        """
        session = self._get_session()
        try:
            # Create or update user profile with questionnaire data
            # Map questionnaire fields to UserProfile model fields
            profile_data = {
                'user_id': int(user_id),  # Convert to int for foreign key
                'monthly_income': questionnaire_data.get('monthly_income', 0),
                'current_savings': questionnaire_data.get('current_savings', 0),
                'current_debt': questionnaire_data.get('total_debt', 0),
                'risk_tolerance': self._map_risk_tolerance(questionnaire_data.get('risk_tolerance', 3)),
                'primary_goal': self._get_primary_goal(questionnaire_data.get('financial_goals', [])),
                'is_complete': True
            }
            
            # Check if profile exists
            existing_profile = session.query(UserProfile).filter_by(user_id=int(user_id)).first()
            
            if existing_profile:
                # Update existing profile
                for key, value in profile_data.items():
                    if hasattr(existing_profile, key):
                        setattr(existing_profile, key, value)
                profile = existing_profile
            else:
                # Create new profile
                profile = UserProfile(**profile_data)
                session.add(profile)
            
            # Create or update onboarding progress
            onboarding_data = {
                'user_id': int(user_id),
                'current_step': 'financial_questionnaire',
                'is_complete': True,
                'completion_percentage': 100,
                'completed_at': datetime.now(timezone.utc)
            }
            
            existing_progress = session.query(OnboardingProgress).filter_by(user_id=int(user_id)).first()
            
            if existing_progress:
                # Update existing progress
                for key, value in onboarding_data.items():
                    if hasattr(existing_progress, key):
                        setattr(existing_progress, key, value)
                progress = existing_progress
            else:
                # Create new progress record
                progress = OnboardingProgress(**onboarding_data)
                session.add(progress)
            
            session.commit()
            session.refresh(profile)
            session.refresh(progress)
            
            logger.info(f"Successfully saved questionnaire data for user_id: {user_id}")
            return {
                'profile': profile.to_dict(),
                'progress': progress.to_dict()
            }
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving questionnaire data for user_id {user_id}: {e}")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"An unexpected error occurred while saving questionnaire data for user_id {user_id}: {e}")
            return None
        finally:
            session.close()

    def _map_risk_tolerance(self, score: int) -> str:
        """Map numeric risk tolerance to string values"""
        if score <= 1:
            return 'conservative'
        elif score <= 3:
            return 'moderate'
        else:
            return 'aggressive'
    
    def _get_primary_goal(self, goals: list) -> str:
        """Get the primary goal from the list of financial goals"""
        if not goals:
            return 'save'
        
        # Priority order for goals
        priority_goals = ['emergency_fund', 'debt_payoff', 'savings', 'investment', 'retirement', 'home_purchase']
        
        for goal in priority_goals:
            if goal in goals:
                return goal
        
        return goals[0] if goals else 'save'

    def track_onboarding_choice(self, user_id, choice):
        # Store in user profile
        user = self.get_user_profile(user_id)
        if user:
            user['onboarding_type'] = choice  # 'brief' or 'detailed'
            self.update_user_profile(user_id, user)
        # Log to analytics (example)
        business_intelligence.track_user_metric(user_id, 'onboarding_choice', 1.0, {'choice': choice})