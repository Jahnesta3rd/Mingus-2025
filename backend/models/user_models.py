from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class User:
    id: str
    email: str
    gdpr_consent_given: bool = False
    consent_timestamp: Optional[datetime] = None


@dataclass
class Subscription:
    user_id: str
    plan_type: str  # 'budget', 'mid_tier', 'professional'
    status: str = 'active'
    created_at: datetime = datetime.utcnow()
    expires_at: datetime = datetime.utcnow() + timedelta(days=30)

