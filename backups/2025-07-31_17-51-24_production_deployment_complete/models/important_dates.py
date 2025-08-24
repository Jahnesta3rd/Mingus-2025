from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class DateType(str, Enum):
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    BILL_DUE = "bill_due"
    PAYDAY = "payday"
    SUBSCRIPTION = "subscription"
    INVESTMENT = "investment"
    LOAN_PAYMENT = "loan_payment"
    SAVINGS_GOAL = "savings_goal"
    TAX_PAYMENT = "tax_payment"
    INSURANCE_PAYMENT = "insurance_payment"
    RENT_MORTGAGE = "rent_mortgage"
    UTILITY_BILL = "utility_bill"
    OTHER = "other"

class DateStatus(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

class ImportantDateBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    date_type: DateType
    date: date
    amount: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=500)
    is_recurring: bool = False
    recurrence_interval: Optional[int] = Field(None, ge=1)
    notification_days_before: Optional[int] = Field(None, ge=0)

class ImportantDateCreate(ImportantDateBase):
    pass

class ImportantDateUpdate(ImportantDateBase):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    date_type: Optional[DateType] = None
    date: Optional[date] = None
    amount: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_interval: Optional[int] = None
    notification_days_before: Optional[int] = None

class ImportantDateInDB(ImportantDateBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    status: DateStatus = DateStatus.GREEN

    class Config:
        from_attributes = True

class ImportantDateResponse(ImportantDateInDB):
    cash_impact: Optional[float] = None
    days_until: Optional[int] = None
    has_sufficient_funds: Optional[bool] = None

class PaginatedResponse(BaseModel):
    items: List[ImportantDateResponse]
    total: int
    page: int
    size: int
    pages: int 