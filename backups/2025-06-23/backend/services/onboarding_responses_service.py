from typing import List, Optional
from datetime import datetime
from supabase import Client
from loguru import logger
from backend.models.onboarding_responses import (
    OnboardingResponseCreate,
    OnboardingResponseUpdate,
    OnboardingResponse,
    OnboardingResponsesStats
)

class OnboardingResponsesService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.responses_table = 'onboarding_responses'

    async def create_response(self, response_data: OnboardingResponseCreate) -> OnboardingResponse:
        """
        Create a new onboarding response.
        Validates the response data using Pydantic model.
        """
        try:
            # Convert response value to JSONB
            response_record = {
                'onboarding_id': str(response_data.onboarding_id),
                'response_type': response_data.response_type,
                'response_value_type': response_data.response_value_type,
                'response_value': response_data.response_value.model_dump(exclude_none=True),
                'metadata': response_data.metadata
            }

            result = await self.supabase.table(self.responses_table)\
                .insert(response_record)\
                .execute()

            return OnboardingResponse(**result.data[0]) if result.data else None

        except Exception as e:
            logger.error(f"Error creating onboarding response: {str(e)}")
            raise

    async def get_response(self, response_id: str) -> Optional[OnboardingResponse]:
        """
        Retrieve a specific onboarding response.
        """
        try:
            result = await self.supabase.table(self.responses_table)\
                .select('*')\
                .eq('id', response_id)\
                .single()\
                .execute()

            return OnboardingResponse(**result.data) if result.data else None

        except Exception as e:
            logger.error(f"Error fetching onboarding response: {str(e)}")
            raise

    async def get_responses_by_onboarding(self, onboarding_id: str) -> List[OnboardingResponse]:
        """
        Retrieve all responses for a specific onboarding session.
        """
        try:
            result = await self.supabase.table(self.responses_table)\
                .select('*')\
                .eq('onboarding_id', onboarding_id)\
                .execute()

            return [OnboardingResponse(**response) for response in result.data] if result.data else []

        except Exception as e:
            logger.error(f"Error fetching onboarding responses: {str(e)}")
            raise

    async def update_response(
        self,
        response_id: str,
        updates: OnboardingResponseUpdate
    ) -> OnboardingResponse:
        """
        Update an existing onboarding response.
        Only allows updating the response value and metadata.
        """
        try:
            update_data = {
                'response_value': updates.response_value.model_dump(exclude_none=True),
                'updated_at': datetime.utcnow().isoformat()
            }
            if updates.metadata is not None:
                update_data['metadata'] = updates.metadata

            result = await self.supabase.table(self.responses_table)\
                .update(update_data)\
                .eq('id', response_id)\
                .execute()

            return OnboardingResponse(**result.data[0]) if result.data else None

        except Exception as e:
            logger.error(f"Error updating onboarding response: {str(e)}")
            raise

    async def delete_response(self, response_id: str) -> bool:
        """
        Delete a specific onboarding response.
        """
        try:
            result = await self.supabase.table(self.responses_table)\
                .delete()\
                .eq('id', response_id)\
                .execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error deleting onboarding response: {str(e)}")
            raise

    async def get_response_stats(self) -> List[OnboardingResponsesStats]:
        """
        Get analytics for onboarding responses using the analytics view.
        """
        try:
            result = await self.supabase.from_('onboarding_responses_analytics')\
                .select('*')\
                .execute()

            return [OnboardingResponsesStats(**stat) for stat in result.data] if result.data else []

        except Exception as e:
            logger.error(f"Error fetching onboarding response stats: {str(e)}")
            raise 