from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, UUID4, field_validator, constr, ConfigDict
from enum import Enum
import re

class FinancialChallengeType(str, Enum):
    DEBT_MANAGEMENT = "debt_management"
    EMERGENCY_SAVINGS = "emergency_savings"
    RETIREMENT_PLANNING = "retirement_planning"
    INVESTMENT_GROWTH = "investment_growth"
    BUDGETING = "budgeting"
    TAX_PLANNING = "tax_planning"

class StressHandlingType(str, Enum):
    BUDGETING = "budgeting"
    AUTOMATION = "automation"
    PROFESSIONAL_HELP = "professional_help"
    EDUCATION = "education"
    TRACKING = "tracking"

class MotivationType(str, Enum):
    FINANCIAL_FREEDOM = "financial_freedom"
    DEBT_FREE = "debt_free"
    RETIREMENT = "retirement"
    WEALTH_BUILDING = "wealth_building"
    SECURITY = "security"

class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class OnboardingBase(BaseModel):
    financial_challenge: FinancialChallengeType
    stress_handling: List[StressHandlingType] = Field(min_length=1, max_length=3)
    motivation: List[MotivationType] = Field(min_length=1, max_length=3)
    monthly_income: float = Field(ge=0)
    monthly_expenses: float = Field(ge=0)
    savings_goal: float = Field(ge=0)
    risk_tolerance: int = Field(ge=1, le=10)
    financial_knowledge: int = Field(ge=1, le=10)
    preferred_contact_method: str = Field(pattern='^(email|sms|both)$')
    contact_info: Optional[str] = None

    @field_validator('monthly_expenses')
    def validate_monthly_expenses(cls, v, values):
        if 'monthly_income' in values.data and v > values.data['monthly_income'] * 2:
            raise ValueError('Monthly expenses cannot exceed twice the monthly income')
        return v

    @field_validator('savings_goal')
    def validate_savings_goal(cls, v, values):
        if 'monthly_income' in values.data and v > values.data['monthly_income'] * 120:  # 10 years of income
            raise ValueError('Savings goal cannot exceed 10 years of income')
        return v

    @field_validator('contact_info')
    def validate_contact_info(cls, v, values):
        if 'preferred_contact_method' in values.data:
            if values.data['preferred_contact_method'] in ['email', 'both']:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
                    raise ValueError('Invalid email format')
            elif values.data['preferred_contact_method'] == 'sms':
                if not re.match(r'^\+?1?\d{10,15}$', v):
                    raise ValueError('Invalid phone number format')
        return v

class OnboardingCreate(OnboardingBase):
    pass

class OnboardingUpdate(BaseModel):
    financial_challenge: Optional[FinancialChallengeType] = None
    stress_handling: Optional[List[StressHandlingType]] = None
    motivation: Optional[List[MotivationType]] = None
    monthly_income: Optional[float] = Field(None, ge=0)
    monthly_expenses: Optional[float] = Field(None, ge=0)
    savings_goal: Optional[float] = Field(None, ge=0)
    risk_tolerance: Optional[int] = Field(None, ge=1, le=10)
    financial_knowledge: Optional[int] = Field(None, ge=1, le=10)
    preferred_contact_method: Optional[str] = Field(None, pattern='^(email|sms|both)$')
    contact_info: Optional[str] = None

class OnboardingResponse(BaseModel):
    id: int
    user_id: str
    financial_challenge: FinancialChallengeType
    stress_handling: List[StressHandlingType]
    motivation: List[MotivationType]
    monthly_income: float
    monthly_expenses: float
    savings_goal: float
    risk_tolerance: int
    financial_knowledge: int
    preferred_contact_method: str
    contact_info: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

class OnboardingStatus(BaseModel):
    is_complete: bool
    missing_fields: List[str]

class OnboardingStats(BaseModel):
    total_profiles: int
    avg_monthly_income: float
    avg_monthly_expenses: float
    avg_savings_goal: float
    avg_risk_tolerance: float
    avg_financial_knowledge: float
    top_challenges: List[dict]
    top_stress_handling: List[dict]
    top_motivations: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "total_profiles": 100,
                "avg_monthly_income": 5000.0,
                "avg_monthly_expenses": 2000.0,
                "avg_savings_goal": 100000.0,
                "avg_risk_tolerance": 5.0,
                "avg_financial_knowledge": 7.0
            }
        }

class AnonymousOnboardingCreate(OnboardingCreate):
    session_id: str
    ip_address: str
    user_agent: str
    referrer: Optional[str] = None

    @field_validator('ip_address')
    def validate_ip_address(cls, v):
        # IPv4
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # IPv6
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        
        if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
            raise ValueError('Invalid IP address format')
        
        if re.match(ipv4_pattern, v):
            # Validate IPv4 octets
            octets = v.split('.')
            if any(not (0 <= int(octet) <= 255) for octet in octets):
                raise ValueError('Invalid IPv4 address')
        
        return v

class AnonymousOnboardingResponse(OnboardingResponse):
    session_id: str
    ip_address: str
    user_agent: str
    referrer: Optional[str]
    created_at: datetime
    converted_to_signup: bool = False
    conversion_date: Optional[datetime] = None
    user_id: Optional[str] = None 