from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, timezone
from enum import Enum

class MockAuth:
    def __init__(self):
        self._users = {}
        self.admin = MockAuthAdmin(self._users)

    async def sign_up(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": credentials["email"],
            "created_at": datetime.now().isoformat()
        }
        self._users[user_id] = user
        return {"user": user, "session": None}

class MockAuthAdmin:
    def __init__(self, users: Dict[str, Dict[str, Any]]):
        self._users = users

    async def delete_user(self, user_id: str) -> None:
        if user_id in self._users:
            del self._users[user_id]

class MockTable:
    def __init__(self, name: str):
        self.name = name
        self.data: List[Dict[str, Any]] = []
        self._filters = []
        self._last_inserted = None
        self._id_counter = 1
        
    def insert(self, record: Dict[str, Any]) -> 'MockTable':
        # Add auto-incrementing id if not present
        if 'id' not in record:
            record['id'] = self._id_counter
            self._id_counter += 1
        # Convert Enum values to strings
        for k, v in record.items():
            if isinstance(v, Enum):
                record[k] = v.value
            elif isinstance(v, list):
                record[k] = [item.value if isinstance(item, Enum) else item for item in v]
        # Add timestamps if not present
        if 'created_at' not in record:
            record['created_at'] = datetime.now(timezone.utc).isoformat()
        if 'updated_at' not in record:
            record['updated_at'] = record['created_at']
        self.data.append(record)
        self._last_inserted = record
        return self
        
    def select(self, *args, **kwargs) -> 'MockTable':
        self._filters = []
        return self
        
    def eq(self, column: str, value: Any) -> 'MockTable':
        self._filters.append(lambda x: x.get(column) == value)
        return self
        
    async def execute(self) -> 'MockResponse':
        if self._last_inserted is not None:
            # If called after insert, return just the last inserted record
            data = [self._last_inserted]
            self._last_inserted = None
            return MockResponse(data)
        filtered_data = self.data
        for filter_func in self._filters:
            filtered_data = [item for item in filtered_data if filter_func(item)]
        return MockResponse(filtered_data)

class MockResponse:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data

class MockSupabaseClient:
    def __init__(self):
        self._tables = {
            'onboarding_responses': MockTable('onboarding_responses'),
            'personalization_analytics': MockTable('personalization_analytics')
        }
        self.auth = MockAuth()

    def clear_data(self):
        """Clear all data from the mock database."""
        self._tables = {
            'onboarding_responses': MockTable('onboarding_responses'),
            'personalization_analytics': MockTable('personalization_analytics')
        }
        self.auth = MockAuth()

    def table(self, name: str) -> MockTable:
        if name not in self._tables:
            self._tables[name] = MockTable(name)
        return self._tables[name]

    async def initialize_tables(self):
        """Initialize tables with test data."""
        # This method can be used to pre-populate tables with test data if needed
        pass

    async def rpc(self, fn_name: str, params: Dict = None) -> Dict[str, Any]:
        """Mock RPC calls."""
        return {"data": [], "error": None}

# Test data generators
def generate_onboarding_response(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Generate a test onboarding response."""
    if not session_id:
        session_id = str(uuid.uuid4())
        
    return {
        'session_id': session_id,
        'financial_challenge': 'DEBT_MANAGEMENT',
        'stress_handling': ['SEEK_ADVICE', 'PLAN'],
        'motivation': ['FINANCIAL_FREEDOM', 'DEBT_FREE'],
        'monthly_income': 5000.0,
        'monthly_expenses': 3000.0,
        'savings_goal': 20000.0,
        'risk_tolerance': 7,
        'financial_knowledge': 6,
        'preferred_contact_method': 'email',
        'contact_info': 'test@example.com',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }

def generate_analytics_event(
    session_id: str,
    event_type: str,
    properties: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate a test analytics event."""
    return {
        'session_id': session_id,
        'event_type': event_type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'properties': properties or {}
    } 