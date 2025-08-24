# services.py
from werkzeug.security import generate_password_hash, check_password_hash
import re

class UserService:
    def __init__(self, supabase_client):
        """Initialize with your existing Supabase client from config"""
        self.supabase = supabase_client
    
    def authenticate_user(self, email, password):
        """Check if user credentials are valid"""
        try:
            response = self.supabase.table('users').select('*').eq('email', email).execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                if check_password_hash(user['password_hash'], password):
                    return user
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Find user by email address"""
        try:
            response = self.supabase.table('users').select('*').eq('email', email).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Get user error: {e}")
            return None
    
    def create_user(self, user_data):
        """Create a new user account"""
        try:
            email = user_data.get('email')
            password = user_data.get('password')
            
            # Basic validation
            if not self._is_valid_email(email):
                return None, "Invalid email format"
            
            if not self._is_valid_password(password):
                return None, "Password must be at least 8 characters"
            
            # Check if user already exists
            if self.get_user_by_email(email):
                return None, "User with this email already exists"
            
            # Hash password
            password_hash = generate_password_hash(password)
            
            # Insert new user into Supabase
            response = self.supabase.table('users').insert({
                'email': email,
                'password_hash': password_hash,
                'is_active': True
            }).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0], "User created successfully"
            else:
                return None, "Failed to create user"
            
        except Exception as e:
            print(f"Create user error: {e}")
            return None, "Failed to create user"
    
    def _is_valid_email(self, email):
        """Basic email validation"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_password(self, password):
        """Basic password validation"""
        return password and len(password) >= 8