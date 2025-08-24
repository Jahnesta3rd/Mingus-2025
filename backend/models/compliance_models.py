from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class AuditLog:
    id: str
    event: str
    timestamp: datetime
    details: Dict[str, Any]


@dataclass
class ConsentRecord:
    id: str
    user_id: str
    consent_type: str
    status: str
    timestamp: datetime


@dataclass
class DataRetentionPolicy:
    id: str
    data_type: str
    retention_period_years: int


