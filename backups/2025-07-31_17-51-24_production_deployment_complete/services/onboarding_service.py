<<<<<<< HEAD
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
=======
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from supabase import Client
from loguru import logger
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    AnonymousOnboardingResponse,
    OnboardingCreate,
    OnboardingUpdate,
    OnboardingResponse,
    OnboardingStatus,
    OnboardingStats
)

class OnboardingService:
    def __init__(self, supabase_client: Client):
        self.db = supabase_client
        self.table = "onboarding"
        self.anonymous_table = "anonymous_onboarding_responses"

    async def create_anonymous_onboarding(self, data: AnonymousOnboardingCreate) -> AnonymousOnboardingResponse:
        """Create an anonymous onboarding response."""
        try:
            result = await self.db.table(self.anonymous_table).insert({
                **data.model_dump(),
                "created_at": datetime.now().isoformat()
            }).execute()

            if result.data:
                return AnonymousOnboardingResponse(**result.data[0])
            raise ValueError("Failed to create anonymous onboarding response")
        except Exception as e:
            logger.error(f"Error creating anonymous onboarding: {str(e)}")
            raise Exception(f"Error creating anonymous onboarding: {str(e)}")

    async def get_anonymous_onboarding(self, session_id: str) -> List[AnonymousOnboardingResponse]:
        """Get all anonymous onboarding responses for a session."""
        try:
            result = await self.db.table(self.anonymous_table)\
                .select("*")\
                .eq("session_id", session_id)\
                .execute()
            return [AnonymousOnboardingResponse(**item) for item in result.data]
        except Exception as e:
            logger.error(f"Error getting anonymous onboarding: {str(e)}")
            raise e

    async def convert_anonymous_to_user(self, session_id: str, user_id: str) -> OnboardingResponse:
        """Convert anonymous onboarding responses to user onboarding."""
        try:
            # Get anonymous responses
            responses = await self.get_anonymous_onboarding(session_id)
            if not responses:
                raise ValueError("No anonymous responses found for this session")

            # Use the most recent response
            latest_response = responses[-1]

            # Create user onboarding profile
            onboarding_data = OnboardingCreate(
                financial_challenge=latest_response.financial_challenge,
                stress_handling=latest_response.stress_handling,
                motivation=latest_response.motivation,
                monthly_income=latest_response.monthly_income,
                monthly_expenses=latest_response.monthly_expenses,
                savings_goal=latest_response.savings_goal,
                risk_tolerance=latest_response.risk_tolerance,
                financial_knowledge=latest_response.financial_knowledge,
                preferred_contact_method=latest_response.preferred_contact_method,
                contact_info=latest_response.contact_info
            )

            result = await self.create_onboarding_profile(user_id, onboarding_data)

            # Mark anonymous responses as converted
            await self.db.table(self.anonymous_table)\
                .update({"converted_to_user_id": user_id})\
                .eq("session_id", session_id)\
                .execute()

            return result
        except Exception as e:
            logger.error(f"Error converting anonymous onboarding: {str(e)}")
            raise e

    async def create_onboarding_profile(self, user_id: str, data: OnboardingCreate) -> OnboardingResponse:
        """Create a user onboarding profile."""
        try:
            # Check if profile already exists
            existing = await self.db.table(self.table)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()

            if existing.data:
                raise ValueError("Onboarding profile already exists for this user")

            result = await self.db.table(self.table).insert({
                "user_id": user_id,
                **data.model_dump(),
                "created_at": datetime.now().isoformat()
            }).execute()

            if result.data:
                return OnboardingResponse(**result.data[0])
            raise ValueError("Failed to create onboarding profile")
        except Exception as e:
            logger.error(f"Error creating onboarding profile: {str(e)}")
            raise e

    async def get_onboarding_profile(self, user_id: str) -> Optional[OnboardingResponse]:
        """Get a user's onboarding profile."""
        try:
            result = await self.db.table(self.table)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()

            if result.data:
                return OnboardingResponse(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting onboarding profile: {str(e)}")
            raise e

    async def update_onboarding_profile(self, user_id: str, data: OnboardingUpdate) -> OnboardingResponse:
        """Update a user's onboarding profile."""
        try:
            result = await self.db.table(self.table)\
                .update({
                    **data.model_dump(exclude_unset=True),
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("user_id", user_id)\
                .execute()

            if result.data:
                return OnboardingResponse(**result.data[0])
            raise ValueError("Failed to update onboarding profile")
        except Exception as e:
            logger.error(f"Error updating onboarding profile: {str(e)}")
            raise e

    async def check_onboarding_status(self, user_id: str) -> OnboardingStatus:
        """Check the onboarding status for a user."""
        try:
            profile = await self.get_onboarding_profile(user_id)
            if not profile:
                return OnboardingStatus.NOT_STARTED
            if profile.updated_at:
                return OnboardingStatus.COMPLETED
            return OnboardingStatus.IN_PROGRESS
        except Exception as e:
            logger.error(f"Error checking onboarding status: {str(e)}")
            raise e

    async def get_onboarding_stats(self) -> OnboardingStats:
        """Get statistics about onboarding profiles."""
        try:
            result = await self.db.table(self.table).select("*").execute()
            profiles = result.data

            if not profiles:
                return OnboardingStats(
                    total_profiles=0,
                    avg_monthly_income=0,
                    avg_monthly_expenses=0,
                    avg_savings_goal=0,
                    avg_risk_tolerance=0,
                    avg_financial_knowledge=0,
                    top_challenges=[],
                    top_stress_handling=[],
                    top_motivations=[]
                )

            # Calculate averages
            total = len(profiles)
            avg_income = sum(p["monthly_income"] for p in profiles) / total
            avg_expenses = sum(p["monthly_expenses"] for p in profiles) / total
            avg_goal = sum(p["savings_goal"] for p in profiles) / total
            avg_risk = sum(p["risk_tolerance"] for p in profiles) / total
            avg_knowledge = sum(p["financial_knowledge"] for p in profiles) / total

            # Calculate top choices
            challenges = {}
            stress = {}
            motivations = {}

            for p in profiles:
                challenges[p["financial_challenge"]] = challenges.get(p["financial_challenge"], 0) + 1
                for s in p["stress_handling"]:
                    stress[s] = stress.get(s, 0) + 1
                for m in p["motivation"]:
                    motivations[m] = motivations.get(m, 0) + 1

            return OnboardingStats(
                total_profiles=total,
                avg_monthly_income=avg_income,
                avg_monthly_expenses=avg_expenses,
                avg_savings_goal=avg_goal,
                avg_risk_tolerance=avg_risk,
                avg_financial_knowledge=avg_knowledge,
                top_challenges=self._get_top_items(challenges),
                top_stress_handling=self._get_top_items(stress),
                top_motivations=self._get_top_items(motivations)
            )
        except Exception as e:
            logger.error(f"Error getting onboarding stats: {str(e)}")
            raise e

    async def get_anonymous_onboarding_stats(self) -> OnboardingStats:
        """Get statistics about anonymous onboarding responses."""
        try:
            result = await self.db.table(self.anonymous_table).select("*").execute()
            return self._calculate_stats(result.data)
        except Exception as e:
            logger.error(f"Error getting anonymous onboarding stats: {str(e)}")
            raise e

    def _calculate_stats(self, profiles: List[Dict[str, Any]]) -> OnboardingStats:
        """Calculate statistics from a list of profiles."""
        if not profiles:
            return OnboardingStats(
                total_profiles=0,
                avg_monthly_income=0,
                avg_monthly_expenses=0,
                avg_savings_goal=0,
                avg_risk_tolerance=0,
                avg_financial_knowledge=0,
                top_challenges=[],
                top_stress_handling=[],
                top_motivations=[]
            )

        total = len(profiles)
        avg_income = sum(p["monthly_income"] for p in profiles) / total
        avg_expenses = sum(p["monthly_expenses"] for p in profiles) / total
        avg_goal = sum(p["savings_goal"] for p in profiles) / total
        avg_risk = sum(p["risk_tolerance"] for p in profiles) / total
        avg_knowledge = sum(p["financial_knowledge"] for p in profiles) / total

        challenges = {}
        stress = {}
        motivations = {}

        for p in profiles:
            challenges[p["financial_challenge"]] = challenges.get(p["financial_challenge"], 0) + 1
            for s in p["stress_handling"]:
                stress[s] = stress.get(s, 0) + 1
            for m in p["motivation"]:
                motivations[m] = motivations.get(m, 0) + 1

        return OnboardingStats(
            total_profiles=total,
            avg_monthly_income=avg_income,
            avg_monthly_expenses=avg_expenses,
            avg_savings_goal=avg_goal,
            avg_risk_tolerance=avg_risk,
            avg_financial_knowledge=avg_knowledge,
            top_challenges=self._get_top_items(challenges),
            top_stress_handling=self._get_top_items(stress),
            top_motivations=self._get_top_items(motivations)
        )

    def _get_top_items(self, items: Dict[str, int], limit: int = 3) -> List[Dict[str, Any]]:
        """Get the top N items from a frequency dictionary."""
        sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)
        return [{"name": k, "count": v} for k, v in sorted_items[:limit]]

    # --- ANALYTICS & DASHBOARD FUNCTIONS ---

    async def count_responses_by_option(self, field: str, table: Optional[str] = None) -> Dict[str, int]:
        """Count responses by a given field (e.g., 'financial_challenge', 'motivation')."""
        table = table or self.table
        result = await self.db.table(table).select(field).execute()
        counts = {}
        for row in result.data:
            value = row.get(field)
            if isinstance(value, list):
                for v in value:
                    counts[v] = counts.get(v, 0) + 1
            else:
                counts[value] = counts.get(value, 0) + 1
        return counts

    async def conversion_rates_by_combination(self, fields: List[str], table: Optional[str] = None) -> Dict[str, float]:
        """Track conversion rates by combinations of field values (e.g., challenge+motivation)."""
        table = table or self.anonymous_table
        anon = await self.db.table(table).select("*").execute()
        combos = {}
        conversions = {}
        for row in anon.data:
            key = tuple(str(row.get(f)) for f in fields)
            combos[key] = combos.get(key, 0) + 1
            if row.get("converted_to_user_id"):
                conversions[key] = conversions.get(key, 0) + 1
        rates = {str(k): conversions.get(k, 0) / v for k, v in combos.items()}
        return rates

    async def time_to_signup_stats(self, table: Optional[str] = None) -> Dict[str, float]:
        """Measure time (in seconds) between onboarding completion and signup."""
        table = table or self.anonymous_table
        anon = await self.db.table(table).select("*").execute()
        times = []
        for row in anon.data:
            if row.get("converted_to_user_id") and row.get("created_at") and row.get("converted_at"):
                t1 = datetime.fromisoformat(row["created_at"])
                t2 = datetime.fromisoformat(row["converted_at"])
                times.append((t2 - t1).total_seconds())
        if not times:
            return {"average": 0, "min": 0, "max": 0}
        return {"average": sum(times)/len(times), "min": min(times), "max": max(times)}

    async def dashboard_aggregates(self, table: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate data for dashboard: top challenges, conversion by motivation, geo distribution."""
        table = table or self.anonymous_table
        # Most common financial challenges
        challenges = await self.count_responses_by_option("financial_challenge", table=table)
        # Conversion rates by motivation
        conv_by_motivation = await self.conversion_rates_by_combination(["motivation"], table=table)
        # Geographic distribution (if IP tracking enabled)
        anon = await self.db.table(table).select("ip_address").execute()
        geo = {}
        for row in anon.data:
            ip = row.get("ip_address")
            if ip:
                geo[ip] = geo.get(ip, 0) + 1
        return {
            "top_challenges": challenges,
            "conversion_by_motivation": conv_by_motivation,
            "geo_distribution": geo
        }

    async def ab_test_results(self, experiment_name: str, table: Optional[str] = None) -> Dict[str, Any]:
        """A/B testing framework for different question options."""
        table = table or self.anonymous_table
        anon = await self.db.table(table).select("ab_group", "converted_to_user_id").execute()
        groups = {}
        conversions = {}
        for row in anon.data:
            group = row.get("ab_group")
            groups[group] = groups.get(group, 0) + 1
            if row.get("converted_to_user_id"):
                conversions[group] = conversions.get(group, 0) + 1
        results = {g: {"total": groups[g], "converted": conversions.get(g, 0), "rate": conversions.get(g, 0)/groups[g] if groups[g] else 0} for g in groups}
        return results

    async def export_onboarding_data(self, format: str = 'csv', table: Optional[str] = None) -> str:
        """Export onboarding data for external analysis (CSV or JSON). Returns file path."""
        import csv, json, os, tempfile
        table = table or self.table
        result = await self.db.table(table).select("*").execute()
        data = result.data
        if format == 'csv':
            fd, path = tempfile.mkstemp(suffix='.csv')
            with os.fdopen(fd, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            return path
        elif format == 'json':
            fd, path = tempfile.mkstemp(suffix='.json')
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f)
            return path
        else:
            raise ValueError('Unsupported export format') 
>>>>>>> 18b195ffe700f2ac1a508d162ad042b3b768c7ae
