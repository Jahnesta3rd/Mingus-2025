from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from ..models.important_dates import (
    ImportantDateCreate,
    ImportantDateUpdate,
    ImportantDateInDB,
    ImportantDateResponse,
    DateStatus,
    PaginatedResponse
)
from loguru import logger
from supabase import Client

class ImportantDatesService:
    def __init__(self, supabase_client: Client):
        self.db = supabase_client
        self.table = "user_important_dates"

    async def get_dates(
        self,
        user_id: str,
        page: int = 1,
        size: int = 10,
        date_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PaginatedResponse:
        try:
            query = self.db.table(self.table).select("*").eq("user_id", user_id)

            if date_type:
                query = query.eq("date_type", date_type)
            if start_date:
                query = query.gte("date", start_date.isoformat())
            if end_date:
                query = query.lte("date", end_date.isoformat())

            # Get total count
            total = len(query.execute().data)
            
            # Apply pagination
            query = query.range((page - 1) * size, page * size - 1)
            
            result = await query.execute()
            
            items = [self._enrich_date_response(ImportantDateInDB(**item)) 
                    for item in result.data]

            return PaginatedResponse(
                items=items,
                total=total,
                page=page,
                size=size,
                pages=(total + size - 1) // size
            )

        except Exception as e:
            logger.error(f"Error fetching dates: {str(e)}")
            raise

    async def create_date(self, user_id: str, date_data: ImportantDateCreate) -> ImportantDateResponse:
        try:
            # Check for duplicates
            existing = await self.db.table(self.table).select("*")\
                .eq("user_id", user_id)\
                .eq("title", date_data.title)\
                .eq("date", date_data.date.isoformat())\
                .execute()

            if existing.data:
                raise ValueError("A date with this title already exists for this day")

            data = {
                **date_data.model_dump(),
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": self._calculate_status(date_data.amount if date_data.amount else 0)
            }

            result = await self.db.table(self.table).insert(data).execute()
            created_date = ImportantDateInDB(**result.data[0])
            response = self._enrich_date_response(created_date)
            return response

        except Exception as e:
            logger.error(f"Error creating date: {str(e)}")
            raise

    async def update_date(
        self,
        user_id: str,
        date_id: int,
        date_data: ImportantDateUpdate
    ) -> ImportantDateResponse:
        try:
            # Verify ownership
            existing = await self.db.table(self.table).select("*")\
                .eq("id", date_id)\
                .eq("user_id", user_id)\
                .execute()

            if not existing.data:
                raise ValueError("Date not found or unauthorized")

            update_data = {
                **date_data.model_dump(exclude_unset=True),
                "updated_at": datetime.utcnow()
            }

            if "amount" in update_data:
                update_data["status"] = self._calculate_status(update_data["amount"])

            result = await self.db.table(self.table)\
                .update(update_data)\
                .eq("id", date_id)\
                .execute()

            updated_date = ImportantDateInDB(**result.data[0])
            response = self._enrich_date_response(updated_date)
            return response

        except Exception as e:
            logger.error(f"Error updating date: {str(e)}")
            raise

    async def delete_date(self, user_id: str, date_id: int) -> bool:
        try:
            # Verify ownership
            existing = await self.db.table(self.table).select("*")\
                .eq("id", date_id)\
                .eq("user_id", user_id)\
                .execute()

            if not existing.data:
                raise ValueError("Date not found or unauthorized")

            await self.db.table(self.table)\
                .delete()\
                .eq("id", date_id)\
                .execute()

            return True

        except Exception as e:
            logger.error(f"Error deleting date: {str(e)}")
            raise

    async def get_upcoming_dates(self, user_id: str, days: int = 90) -> List[ImportantDateResponse]:
        try:
            today = datetime.utcnow().date()
            end_date = today + timedelta(days=days)
            
            # First get all dates
            result = await self.db.table(self.table).select("*")\
                .eq("user_id", user_id)\
                .execute()

            # Filter dates in memory to handle date comparison correctly
            filtered_dates = []
            for item in result.data:
                date_obj = ImportantDateInDB(**item)
                if today <= date_obj.date <= end_date:
                    filtered_dates.append(date_obj)

            # Sort by date
            filtered_dates.sort(key=lambda x: x.date)
            
            return [self._enrich_date_response(date) for date in filtered_dates]

        except Exception as e:
            logger.error(f"Error fetching upcoming dates: {str(e)}")
            raise

    async def analyze_cash_impact(
        self,
        user_id: str,
        balance: float,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ImportantDateResponse]:
        try:
            query = self.db.table(self.table).select("*").eq("user_id", user_id)
            
            if start_date:
                query = query.gte("date", start_date.isoformat())
            if end_date:
                query = query.lte("date", end_date.isoformat())
                
            result = await query.order("date").execute()
            
            # Use a set to track unique dates
            seen_dates = set()
            dates = []
            running_balance = balance
            
            for item in result.data:
                date_obj = ImportantDateInDB(**item)
                date_key = (date_obj.date, date_obj.title)  # Use date and title as unique key
                
                if date_key not in seen_dates:
                    seen_dates.add(date_key)
                    response = self._enrich_date_response(date_obj)
                    
                    if date_obj.amount:
                        response.cash_impact = date_obj.amount
                        response.has_sufficient_funds = running_balance >= date_obj.amount
                        running_balance = running_balance - date_obj.amount
                    
                    dates.append(response)
            
            return dates

        except Exception as e:
            logger.error(f"Error analyzing cash impact: {str(e)}")
            raise

    def _calculate_status(self, amount: float) -> DateStatus:
        # This is a placeholder implementation
        # In a real application, this would consider the user's financial situation
        if amount <= 100:
            return DateStatus.GREEN
        elif amount <= 500:
            return DateStatus.YELLOW
        return DateStatus.RED

    def _enrich_date_response(self, date: ImportantDateInDB) -> ImportantDateResponse:
        response = ImportantDateResponse(**date.model_dump())
        response.days_until = (date.date - datetime.utcnow().date()).days
        return response 