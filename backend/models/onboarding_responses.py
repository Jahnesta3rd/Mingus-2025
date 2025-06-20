from datetime import datetime
from typing import Dict, Optional, Union, List
from pydantic import BaseModel, Field, UUID4
from enum import Enum

class ResponseType(str, Enum):
    INCOME = 'income'
    EXPENSE = 'expense'
    SAVINGS_GOAL = 'savings_goal'
    DEBT = 'debt'
    INVESTMENT = 'investment'
    RISK_TOLERANCE = 'risk_tolerance'
    FINANCIAL_KNOWLEDGE = 'financial_knowledge'
    SPENDING_HABIT = 'spending_habit'
    EMERGENCY_FUND = 'emergency_fund'
    RETIREMENT_PLAN = 'retirement_plan'

class ResponseValueType(str, Enum):
    NUMBER = 'number'
    TEXT = 'text'
    BOOLEAN = 'boolean'
    DATE = 'date'
    RANGE = 'range'
    MULTIPLE_CHOICE = 'multiple_choice'
    SINGLE_CHOICE = 'single_choice'

class ResponseValue(BaseModel):
    """Base model for response values with type-specific validation"""
    number: Optional[float] = None
    text: Optional[str] = None
    boolean: Optional[bool] = None
    date: Optional[datetime] = None
    range: Optional[Dict[str, float]] = None  # e.g., {"min": 1000, "max": 5000}
    choices: Optional[List[str]] = None  # For both multiple and single choice

class OnboardingResponseCreate(BaseModel):
    """Request model for creating an onboarding response."""
    onboarding_id: UUID4 = Field(..., description="ID of the user's onboarding session")
    response_type: ResponseType = Field(..., description="Category of the response")
    response_value_type: ResponseValueType = Field(..., description="Type of the response value")
    response_value: ResponseValue = Field(..., description="The actual response value")
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata about the response"
    )

class OnboardingResponseUpdate(BaseModel):
    """Request model for updating an onboarding response."""
    response_value: ResponseValue = Field(..., description="The updated response value")
    metadata: Optional[Dict] = Field(None, description="Updated metadata")

class OnboardingResponse(BaseModel):
    """Response model for onboarding response data."""
    id: UUID4
    onboarding_id: UUID4
    response_type: ResponseType
    response_value_type: ResponseValueType
    response_value: ResponseValue
    metadata: Dict
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "onboarding_id": "123e4567-e89b-12d3-a456-426614174001",
                "response_type": "income",
                "response_value_type": "range",
                "response_value": {
                    "range": {"min": 5000, "max": 7000}
                },
                "metadata": {
                    "frequency": "monthly",
                    "confidence": "high"
                },
                "created_at": "2025-06-03T10:00:00Z",
                "updated_at": "2025-06-03T10:00:00Z"
            }
        }

class OnboardingResponsesStats(BaseModel):
    """Response model for onboarding responses analytics."""
    response_type: ResponseType
    response_value_type: ResponseValueType
    response_count: int
    unique_users: int
    percentage: float

    class Config:
        json_schema_extra = {
            "example": {
                "response_type": "income",
                "response_value_type": "range",
                "response_count": 100,
                "unique_users": 50,
                "percentage": 25.5
            }
        } 