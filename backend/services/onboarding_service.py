from typing import Optional, Dict, Any
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend.models.user_profile import UserProfile
from backend.models.onboarding_progress import OnboardingProgress
import json

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

            onboarding_record.current_step = step_name
            onboarding_record.is_completed = is_completed
            
            if responses:
                if onboarding_record.responses:
                    onboarding_record.responses.update(responses)
                else:
                    onboarding_record.responses = responses
            
            if is_completed:
                onboarding_record.completed_at = datetime.now(timezone.utc)

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