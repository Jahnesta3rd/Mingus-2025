from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.models.onboarding import (
    AnonymousOnboardingResponse,
    FinancialChallengeType,
    MotivationType
)
from supabase.client import Client
from collections import defaultdict

class PersonalizationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_user_responses(self, session_id: str) -> List[AnonymousOnboardingResponse]:
        """Get all onboarding responses for a session."""
        try:
            result = self.supabase.table('anonymous_onboarding_responses').select('*').eq('session_id', session_id).execute()
            return [AnonymousOnboardingResponse(**item) for item in result.data] if result.data else []
        except Exception as e:
            raise Exception(f"Error fetching user responses: {str(e)}")

    def get_testimonial(self, financial_challenge: FinancialChallengeType) -> Dict[str, str]:
        """Get personalized testimonial based on financial challenge."""
        testimonials = {
            FinancialChallengeType.EMERGENCY_SAVINGS: {
                "author": "Sarah M.",
                "role": "Teacher",
                "quote": "I never thought I could build an emergency fund on my salary. Mingus helped me save my first $5,000 in just 6 months!",
                "impact": "Now I sleep better knowing I'm prepared for unexpected expenses."
            },
            FinancialChallengeType.MULTIPLE_INCOME: {
                "author": "James K.",
                "role": "Freelance Designer",
                "quote": "Managing income from multiple clients was a nightmare until I found Mingus. Now I have a clear view of all my revenue streams.",
                "impact": "I've increased my total income by 40% through better income stream management."
            },
            FinancialChallengeType.DEBT: {
                "author": "Maria R.",
                "role": "Small Business Owner",
                "quote": "Mingus helped me create a realistic debt payoff plan that didn't sacrifice my business growth.",
                "impact": "I paid off $35,000 in business debt while growing my revenue."
            },
            FinancialChallengeType.MAJOR_EXPENSES: {
                "author": "David L.",
                "role": "Software Engineer",
                "quote": "Planning for my wedding seemed impossible until Mingus helped me break down the expenses and create a saving strategy.",
                "impact": "We had our dream wedding without going into debt."
            }
        }
        return testimonials.get(financial_challenge, testimonials[FinancialChallengeType.EMERGENCY_SAVINGS])

    def get_cta_text(self, motivation: MotivationType) -> str:
        """Get personalized CTA button text based on motivation."""
        cta_texts = {
            MotivationType.FAMILY_GOALS: "Start Planning for My Family",
            MotivationType.PERSONAL_GROWTH: "Begin My Growth Journey",
            MotivationType.COMMUNITY_IMPACT: "Connect with My Community",
            MotivationType.FINANCIAL_FREEDOM: "Achieve Financial Freedom"
        }
        return cta_texts.get(motivation, "Get Started Now")

    def track_personalization_conversion(
        self,
        session_id: str,
        financial_challenge: FinancialChallengeType,
        motivation: MotivationType,
        converted: bool
    ) -> None:
        """Track which personalizations lead to conversions."""
        try:
            # Convert enum values to strings
            data = {
                'session_id': session_id,
                'financial_challenge': str(financial_challenge.value),
                'motivation': str(motivation.value),
                'converted': converted,
                'timestamp': datetime.now().isoformat()
            }
            self.supabase.table('personalization_analytics').insert(data).execute()
        except Exception as e:
            raise Exception(f"Error tracking personalization conversion: {str(e)}")

    def get_personalization_stats(self) -> Dict[str, Any]:
        """Get analytics on which personalizations lead to conversions."""
        try:
            # Get all analytics data
            result = self.supabase.table('personalization_analytics').select('*').execute()
            data = result.data if result.data else []
            
            # Process financial challenge stats
            challenge_stats = defaultdict(lambda: {'total': 0, 'conversions': 0})
            for row in data:
                challenge = row['financial_challenge']
                challenge_stats[challenge]['total'] += 1
                if row['converted']:
                    challenge_stats[challenge]['conversions'] += 1
            
            # Process motivation stats
            motivation_stats = defaultdict(lambda: {'total': 0, 'conversions': 0})
            for row in data:
                motivation = row['motivation']
                motivation_stats[motivation]['total'] += 1
                if row['converted']:
                    motivation_stats[motivation]['conversions'] += 1
            
            # Calculate conversion rates
            stats = {
                'financial_challenges': self._calculate_rates(challenge_stats),
                'motivations': self._calculate_rates(motivation_stats)
            }
            
            return stats
        except Exception as e:
            raise Exception(f"Error getting personalization stats: {str(e)}")

    def _calculate_rates(self, stats: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, float]]:
        """Calculate conversion rates from raw counts."""
        result = {}
        for category, data in stats.items():
            total = data['total']
            conversions = data['conversions']
            result[category] = {
                'total': total,
                'conversions': conversions,
                'conversion_rate': (conversions / total) if total > 0 else 0
            }
        return result 