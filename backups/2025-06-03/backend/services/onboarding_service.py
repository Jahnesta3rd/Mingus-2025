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