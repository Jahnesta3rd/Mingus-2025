"""
Mock Services for MINGUS Application Development
Provides mock implementations of external services for development and testing
"""

import os
import json
import logging
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# =====================================================
# DATA CLASSES FOR MOCK MESSAGES
# =====================================================

@dataclass
class MockSMSMessage:
    """Mock SMS message data class"""
    sid: str
    to: str
    from_: str
    body: str
    status: str
    direction: str
    date_created: datetime
    date_sent: Optional[datetime]
    date_updated: datetime
    error_code: Optional[str]
    error_message: Optional[str]
    price: Optional[str]
    price_unit: Optional[str]
    uri: str
    account_sid: str
    num_media: str
    num_segments: str
    api_version: str
    subresource_uris: Dict[str, str]

@dataclass
class MockEmailMessage:
    """Mock email message data class"""
    id: str
    to: List[str]
    from_: str
    subject: str
    html_body: Optional[str]
    text_body: Optional[str]
    attachments: List[Dict[str, Any]]
    status: str
    date_created: datetime
    date_sent: Optional[datetime]
    error_code: Optional[str]
    error_message: Optional[str]

# =====================================================
# MOCK TWILIO SERVICE
# =====================================================

class MockTwilioService:
    """Mock Twilio service for SMS functionality"""
    
    def __init__(self):
        self.account_sid = "dev_account_sid"
        self.auth_token = "dev_auth_token"
        self.phone_number = "+1234567890"
        self.messages = []
        self.log_file = "logs/mock_twilio.log"
        self.data_dir = "data/mock_twilio"
        
        # Create directories
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing messages
        self._load_messages()
    
    def send_sms(self, to: str, from_: str, body: str) -> MockSMSMessage:
        """Send a mock SMS message"""
        try:
            # Generate unique SID
            sid = f"SM{str(uuid.uuid4()).replace('-', '')[:32].upper()}"
            
            # Create message
            now = datetime.utcnow()
            message = MockSMSMessage(
                sid=sid,
                to=to,
                from_=from_,
                body=body,
                status="delivered",
                direction="outbound-api",
                date_created=now,
                date_sent=now,
                date_updated=now,
                error_code=None,
                error_message=None,
                price="0.00",
                price_unit="USD",
                uri=f"/2010-04-01/Accounts/{self.account_sid}/Messages/{sid}.json",
                account_sid=self.account_sid,
                num_media="0",
                num_segments="1",
                api_version="2010-04-01",
                subresource_uris={
                    "media": f"/2010-04-01/Accounts/{self.account_sid}/Messages/{sid}/Media.json"
                }
            )
            
            # Store message
            self.messages.append(message)
            self._save_message(message)
            self._log_message(message)
            
            logger.info(f"Mock SMS sent: {to} -> {body[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"Error sending mock SMS: {e}")
            raise
    
    def get_message(self, sid: str) -> Optional[MockSMSMessage]:
        """Get a mock SMS message by SID"""
        for message in self.messages:
            if message.sid == sid:
                return message
        return None
    
    def list_messages(self, to: Optional[str] = None, from_: Optional[str] = None) -> List[MockSMSMessage]:
        """List mock SMS messages with optional filtering"""
        filtered_messages = self.messages
        
        if to:
            filtered_messages = [m for m in filtered_messages if m.to == to]
        
        if from_:
            filtered_messages = [m for m in filtered_messages if m.from_ == from_]
        
        return filtered_messages
    
    def _save_message(self, message: MockSMSMessage):
        """Save message to filesystem"""
        try:
            message_file = os.path.join(self.data_dir, f"{message.sid}.json")
            with open(message_file, 'w') as f:
                json.dump(asdict(message), f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Error saving mock SMS message: {e}")
    
    def _load_messages(self):
        """Load messages from filesystem"""
        try:
            for file_path in Path(self.data_dir).glob("*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Convert date strings back to datetime objects
                    for date_field in ['date_created', 'date_sent', 'date_updated']:
                        if data.get(date_field):
                            data[date_field] = datetime.fromisoformat(data[date_field])
                    message = MockSMSMessage(**data)
                    self.messages.append(message)
        except Exception as e:
            logger.error(f"Error loading mock SMS messages: {e}")
    
    def _log_message(self, message: MockSMSMessage):
        """Log message to file"""
        try:
            with open(self.log_file, 'a') as f:
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'send_sms',
                    'message': asdict(message)
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging mock SMS message: {e}")

# =====================================================
# MOCK RESEND SERVICE
# =====================================================

class MockResendService:
    """Mock Resend service for email functionality"""
    
    def __init__(self):
        self.api_key = "dev_api_key"
        self.domain = "mingus.dev"
        self.emails = []
        self.log_file = "logs/mock_resend.log"
        self.data_dir = "data/mock_resend"
        
        # Create directories
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing emails
        self._load_emails()
    
    def send_email(self, 
                  to: List[str], 
                  from_: str, 
                  subject: str, 
                  html_body: Optional[str] = None, 
                  text_body: Optional[str] = None, 
                  attachments: Optional[List[Dict[str, Any]]] = None) -> MockEmailMessage:
        """Send a mock email"""
        try:
            # Generate unique ID
            email_id = str(uuid.uuid4())
            
            # Create email
            now = datetime.utcnow()
            email = MockEmailMessage(
                id=email_id,
                to=to,
                from_=from_,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                attachments=attachments or [],
                status="delivered",
                date_created=now,
                date_sent=now,
                error_code=None,
                error_message=None
            )
            
            # Store email
            self.emails.append(email)
            self._save_email(email)
            self._log_email(email)
            
            logger.info(f"Mock email sent: {to} -> {subject}")
            return email
            
        except Exception as e:
            logger.error(f"Error sending mock email: {e}")
            raise
    
    def get_email(self, email_id: str) -> Optional[MockEmailMessage]:
        """Get a mock email by ID"""
        for email in self.emails:
            if email.id == email_id:
                return email
        return None
    
    def list_emails(self, to: Optional[str] = None, from_: Optional[str] = None) -> List[MockEmailMessage]:
        """List mock emails with optional filtering"""
        filtered_emails = self.emails
        
        if to:
            filtered_emails = [e for e in filtered_emails if to in e.to]
        
        if from_:
            filtered_emails = [e for e in filtered_emails if e.from_ == from_]
        
        return filtered_emails
    
    def _save_email(self, email: MockEmailMessage):
        """Save email to filesystem"""
        try:
            email_file = os.path.join(self.data_dir, f"{email.id}.json")
            with open(email_file, 'w') as f:
                json.dump(asdict(email), f, default=str, indent=2)
            
            # Save HTML content separately if present
            if email.html_body:
                html_file = os.path.join(self.data_dir, f"{email.id}.html")
                with open(html_file, 'w') as f:
                    f.write(email.html_body)
            
            # Save text content separately if present
            if email.text_body:
                text_file = os.path.join(self.data_dir, f"{email.id}.txt")
                with open(text_file, 'w') as f:
                    f.write(email.text_body)
                    
        except Exception as e:
            logger.error(f"Error saving mock email: {e}")
    
    def _load_emails(self):
        """Load emails from filesystem"""
        try:
            for file_path in Path(self.data_dir).glob("*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Convert date strings back to datetime objects
                    for date_field in ['date_created', 'date_sent']:
                        if data.get(date_field):
                            data[date_field] = datetime.fromisoformat(data[date_field])
                    email = MockEmailMessage(**data)
                    self.emails.append(email)
        except Exception as e:
            logger.error(f"Error loading mock emails: {e}")
    
    def _log_email(self, email: MockEmailMessage):
        """Log email to file"""
        try:
            with open(self.log_file, 'a') as f:
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': 'send_email',
                    'email': asdict(email)
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging mock email: {e}")

# =====================================================
# MOCK SUPABASE SERVICE
# =====================================================

class MockSupabaseService:
    """Mock Supabase service for database operations"""
    
    def __init__(self):
        self.url = "https://dev.supabase.co"
        self.key = "dev_key"
        self.data_dir = "data/mock_supabase"
        self.tables = {}
        
        # Create directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def query(self, table: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query mock data from a table"""
        try:
            if table not in self.tables:
                return []
            
            data = self.tables[table].copy()
            
            # Apply filters if provided
            if query:
                data = self._apply_filters(data, query)
            
            logger.info(f"Mock Supabase query: {table} -> {len(data)} records")
            return data
            
        except Exception as e:
            logger.error(f"Error in mock Supabase query: {e}")
            return []
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into a mock table"""
        try:
            if table not in self.tables:
                self.tables[table] = []
            
            # Add ID if not present
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            
            # Add timestamps
            now = datetime.utcnow().isoformat()
            if 'created_at' not in data:
                data['created_at'] = now
            data['updated_at'] = now
            
            # Insert data
            self.tables[table].append(data)
            self._save_table(table)
            
            logger.info(f"Mock Supabase insert: {table} -> {data.get('id')}")
            return data
            
        except Exception as e:
            logger.error(f"Error in mock Supabase insert: {e}")
            raise
    
    def update(self, table: str, data: Dict[str, Any], query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Update data in a mock table"""
        try:
            if table not in self.tables:
                return []
            
            # Add updated timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            updated_records = []
            
            for i, record in enumerate(self.tables[table]):
                # Check if record matches query
                if query and not self._record_matches_query(record, query):
                    continue
                
                # Update record
                record.update(data)
                updated_records.append(record)
            
            if updated_records:
                self._save_table(table)
            
            logger.info(f"Mock Supabase update: {table} -> {len(updated_records)} records")
            return updated_records
            
        except Exception as e:
            logger.error(f"Error in mock Supabase update: {e}")
            return []
    
    def delete(self, table: str, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Delete data from a mock table"""
        try:
            if table not in self.tables:
                return []
            
            deleted_records = []
            remaining_records = []
            
            for record in self.tables[table]:
                # Check if record matches query
                if query and not self._record_matches_query(record, query):
                    remaining_records.append(record)
                else:
                    deleted_records.append(record)
            
            # Update table
            self.tables[table] = remaining_records
            self._save_table(table)
            
            logger.info(f"Mock Supabase delete: {table} -> {len(deleted_records)} records")
            return deleted_records
            
        except Exception as e:
            logger.error(f"Error in mock Supabase delete: {e}")
            return []
    
    def _apply_filters(self, data: List[Dict[str, Any]], query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to data"""
        filtered_data = data
        
        for key, value in query.items():
            if key.startswith('eq.'):
                field = key[3:]
                filtered_data = [record for record in filtered_data if record.get(field) == value]
            elif key.startswith('gt.'):
                field = key[3:]
                filtered_data = [record for record in filtered_data if record.get(field, 0) > value]
            elif key.startswith('lt.'):
                field = key[3:]
                filtered_data = [record for record in filtered_data if record.get(field, 0) < value]
            elif key.startswith('gte.'):
                field = key[3:]
                filtered_data = [record for record in filtered_data if record.get(field, 0) >= value]
            elif key.startswith('lte.'):
                field = key[3:]
                filtered_data = [record for record in filtered_data if record.get(field, 0) <= value]
            elif key.startswith('neq.'):
                field = key[4:]
                filtered_data = [record for record in filtered_data if record.get(field) != value]
            elif key.startswith('like.'):
                field = key[5:]
                filtered_data = [record for record in filtered_data if value in str(record.get(field, ''))]
            elif key.startswith('ilike.'):
                field = key[6:]
                filtered_data = [record for record in filtered_data if value.lower() in str(record.get(field, '')).lower()]
        
        return filtered_data
    
    def _record_matches_query(self, record: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if a record matches a query"""
        for key, value in query.items():
            if key.startswith('eq.'):
                field = key[3:]
                if record.get(field) != value:
                    return False
            elif key.startswith('gt.'):
                field = key[3:]
                if record.get(field, 0) <= value:
                    return False
            elif key.startswith('lt.'):
                field = key[3:]
                if record.get(field, 0) >= value:
                    return False
            # Add more operators as needed
        return True
    
    def _save_table(self, table: str):
        """Save table data to filesystem"""
        try:
            table_file = os.path.join(self.data_dir, f"{table}.json")
            with open(table_file, 'w') as f:
                json.dump(self.tables[table], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving mock Supabase table {table}: {e}")
    
    def _load_data(self):
        """Load data from filesystem"""
        try:
            for file_path in Path(self.data_dir).glob("*.json"):
                table_name = file_path.stem
                with open(file_path, 'r') as f:
                    self.tables[table_name] = json.load(f)
        except Exception as e:
            logger.error(f"Error loading mock Supabase data: {e}")

# =====================================================
# GLOBAL INSTANCES
# =====================================================

# Create global instances
mock_twilio = MockTwilioService()
mock_resend = MockResendService()
mock_supabase = MockSupabaseService()

# =====================================================
# GETTER FUNCTIONS
# =====================================================

def get_mock_twilio_service() -> MockTwilioService:
    """Get the mock Twilio service instance"""
    return mock_twilio

def get_mock_resend_service() -> MockResendService:
    """Get the mock Resend service instance"""
    return mock_resend

def get_mock_supabase_service() -> MockSupabaseService:
    """Get the mock Supabase service instance"""
    return mock_supabase

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def clear_mock_data():
    """Clear all mock data (useful for testing)"""
    mock_twilio.messages.clear()
    mock_resend.emails.clear()
    mock_supabase.tables.clear()
    
    # Clear files
    import shutil
    for service_dir in ["data/mock_twilio", "data/mock_resend", "data/mock_supabase"]:
        if os.path.exists(service_dir):
            shutil.rmtree(service_dir)
            os.makedirs(service_dir, exist_ok=True)

def get_mock_service_status() -> Dict[str, Any]:
    """Get status of all mock services"""
    return {
        'twilio': {
            'messages_count': len(mock_twilio.messages),
            'log_file': mock_twilio.log_file,
            'data_dir': mock_twilio.data_dir
        },
        'resend': {
            'emails_count': len(mock_resend.emails),
            'log_file': mock_resend.log_file,
            'data_dir': mock_resend.data_dir
        },
        'supabase': {
            'tables_count': len(mock_supabase.tables),
            'tables': list(mock_supabase.tables.keys()),
            'data_dir': mock_supabase.data_dir
        }
    } 