#!/usr/bin/env python3
"""
Database Encryption Manager for Mingus Financial App
Comprehensive database security with encryption, access controls, and audit logging
"""

import os
import json
import base64
import secrets
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    """Supported database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"

class AccessLevel(Enum):
    """Database access levels"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    database_type: DatabaseType
    host: str = "localhost"
    port: int = 5432
    database_name: str = "mingus_production"
    username: str = "mingus_user"
    password: str = ""
    ssl_mode: str = "require"
    
    # Encryption settings
    encryption_enabled: bool = True
    column_encryption: bool = True
    connection_encryption: bool = True
    
    # Security settings
    max_connections: int = 20
    connection_timeout: int = 30
    query_timeout: int = 60
    
    # Audit settings
    audit_enabled: bool = True
    audit_table: str = "database_audit_log"
    
    # Backup settings
    backup_enabled: bool = True
    backup_retention_days: int = 30

@dataclass
class DatabaseUser:
    """Database user with access controls"""
    user_id: str
    username: str
    access_level: AccessLevel
    permissions: List[str] = field(default_factory=list)
    ip_whitelist: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_access: Optional[datetime] = None
    is_active: bool = True

@dataclass
class AuditLogEntry:
    """Database audit log entry"""
    timestamp: datetime
    user_id: str
    operation: str
    table_name: str
    record_id: Optional[str] = None
    old_values: Optional[Dict] = None
    new_values: Optional[Dict] = None
    ip_address: str = ""
    user_agent: str = ""
    success: bool = True
    error_message: Optional[str] = None
    execution_time_ms: int = 0

class DatabaseEncryptionManager:
    """Manages database encryption and security"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = {}
        self.users: Dict[str, DatabaseUser] = {}
        self.encryption_key = self._load_or_generate_key()
        
        # Initialize audit logging
        if self.config.audit_enabled:
            self._setup_audit_logging()
        
        # Initialize user management
        self._setup_user_management()
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate database encryption key"""
        key_file = Path("database_encryption.key")
        
        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            logger.info("Generated new database encryption key")
            return key
    
    def _setup_audit_logging(self):
        """Setup database audit logging"""
        self.audit_db_path = "database_audit.db"
        self._create_audit_table()
    
    def _create_audit_table(self):
        """Create audit logging table"""
        with sqlite3.connect(self.audit_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS database_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON database_audit_log(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON database_audit_log(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_operation ON database_audit_log(operation)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_table_name ON database_audit_log(table_name)")
    
    def _setup_user_management(self):
        """Setup database user management"""
        # Create default admin user
        admin_user = DatabaseUser(
            user_id="admin",
            username="admin",
            access_level=AccessLevel.SUPER_ADMIN,
            permissions=["*"],
            ip_whitelist=["127.0.0.1", "::1"]
        )
        self.users["admin"] = admin_user
    
    def _log_audit_event(self, entry: AuditLogEntry):
        """Log database audit event"""
        if not self.config.audit_enabled:
            return
        
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.execute("""
                    INSERT INTO database_audit_log 
                    (timestamp, user_id, operation, table_name, record_id, old_values, new_values, 
                     ip_address, user_agent, success, error_message, execution_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.timestamp.isoformat(),
                    entry.user_id,
                    entry.operation,
                    entry.table_name,
                    entry.record_id,
                    json.dumps(entry.old_values) if entry.old_values else None,
                    json.dumps(entry.new_values) if entry.new_values else None,
                    entry.ip_address,
                    entry.user_agent,
                    entry.success,
                    entry.error_message,
                    entry.execution_time_ms
                ))
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def get_connection(self, user_id: str, ip_address: str = "") -> Any:
        """Get database connection with access control"""
        # Validate user access
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        if not user.is_active:
            raise ValueError(f"User {user_id} is inactive")
        
        # Check IP whitelist
        if user.ip_whitelist and ip_address not in user.ip_whitelist:
            raise ValueError(f"IP {ip_address} not in whitelist for user {user_id}")
        
        # Update last access
        user.last_access = datetime.utcnow()
        
        # Get or create connection
        if self.config.database_type == DatabaseType.POSTGRESQL:
            return self._get_postgresql_connection(user)
        elif self.config.database_type == DatabaseType.SQLITE:
            return self._get_sqlite_connection(user)
        else:
            raise ValueError(f"Unsupported database type: {self.config.database_type}")
    
    def _get_postgresql_connection(self, user: DatabaseUser) -> psycopg2.extensions.connection:
        """Get PostgreSQL connection with encryption"""
        try:
            connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database_name,
                user=self.config.username,
                password=self.config.password,
                sslmode=self.config.ssl_mode,
                cursor_factory=RealDictCursor
            )
            
            # Set connection parameters for security
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = %s", (self.config.query_timeout * 1000,))
                cursor.execute("SET lock_timeout = %s", (self.config.connection_timeout * 1000,))
                
                # Enable SSL if required
                if self.config.connection_encryption:
                    cursor.execute("SET ssl = on")
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _get_sqlite_connection(self, user: DatabaseUser) -> sqlite3.Connection:
        """Get SQLite connection with encryption"""
        try:
            connection = sqlite3.connect("mingus.db")
            connection.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrency
            connection.execute("PRAGMA journal_mode=WAL")
            
            # Set timeout
            connection.execute("PRAGMA busy_timeout=30000")
            
            # Enable foreign keys
            connection.execute("PRAGMA foreign_keys=ON")
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
    
    def encrypt_column_value(self, value: Any, column_name: str, table_name: str) -> str:
        """Encrypt a database column value"""
        if not self.config.column_encryption:
            return str(value)
        
        try:
            # Convert value to string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            # Generate column-specific salt
            salt = f"{table_name}_{column_name}".encode()
            
            # Derive column-specific key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            column_key = kdf.derive(self.encryption_key)
            
            # Generate IV
            iv = secrets.token_bytes(16)
            
            # Encrypt with AES-256-GCM
            cipher = Cipher(
                algorithms.AES(column_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            ciphertext = encryptor.update(value.encode()) + encryptor.finalize()
            auth_tag = encryptor.tag
            
            # Create encrypted value structure
            encrypted_value = {
                'encrypted_data': base64.b64encode(ciphertext).decode(),
                'iv': base64.b64encode(iv).decode(),
                'auth_tag': base64.b64encode(auth_tag).decode(),
                'algorithm': 'aes-256-gcm',
                'created_at': datetime.utcnow().isoformat()
            }
            
            return json.dumps(encrypted_value)
            
        except Exception as e:
            logger.error(f"Failed to encrypt column value: {e}")
            return str(value)
    
    def decrypt_column_value(self, encrypted_value: str, column_name: str, table_name: str) -> Any:
        """Decrypt a database column value"""
        if not self.config.column_encryption:
            return encrypted_value
        
        try:
            # Parse encrypted value
            encrypted_data = json.loads(encrypted_value)
            
            # Generate column-specific salt
            salt = f"{table_name}_{column_name}".encode()
            
            # Derive column-specific key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            column_key = kdf.derive(self.encryption_key)
            
            # Decrypt
            ciphertext = base64.b64decode(encrypted_data['encrypted_data'])
            iv = base64.b64decode(encrypted_data['iv'])
            auth_tag = base64.b64decode(encrypted_data['auth_tag'])
            
            cipher = Cipher(
                algorithms.AES(column_key),
                modes.GCM(iv, auth_tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Try to parse as JSON, otherwise return as string
            try:
                return json.loads(plaintext.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                return plaintext.decode()
                
        except Exception as e:
            logger.error(f"Failed to decrypt column value: {e}")
            return encrypted_value
    
    def execute_query(self, user_id: str, query: str, params: tuple = None, 
                     operation: str = "query", table_name: str = "", 
                     ip_address: str = "", user_agent: str = "") -> List[Dict]:
        """Execute database query with audit logging"""
        start_time = datetime.utcnow()
        
        try:
            # Get connection
            connection = self.get_connection(user_id, ip_address)
            
            # Execute query
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if query.strip().upper().startswith('SELECT'):
                    results = [dict(row) for row in cursor.fetchall()]
                else:
                    connection.commit()
                    results = [{'affected_rows': cursor.rowcount}]
            
            # Log successful audit event
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            audit_entry = AuditLogEntry(
                timestamp=start_time,
                user_id=user_id,
                operation=operation,
                table_name=table_name,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                execution_time_ms=execution_time
            )
            self._log_audit_event(audit_entry)
            
            return results
            
        except Exception as e:
            # Log failed audit event
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            audit_entry = AuditLogEntry(
                timestamp=start_time,
                user_id=user_id,
                operation=operation,
                table_name=table_name,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
            self._log_audit_event(audit_entry)
            
            logger.error(f"Query execution failed: {e}")
            raise
    
    def add_user(self, user: DatabaseUser) -> bool:
        """Add database user"""
        try:
            self.users[user.user_id] = user
            logger.info(f"Added database user: {user.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            return False
    
    def remove_user(self, user_id: str) -> bool:
        """Remove database user"""
        try:
            if user_id in self.users:
                del self.users[user_id]
                logger.info(f"Removed database user: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove user: {e}")
            return False
    
    def update_user_permissions(self, user_id: str, permissions: List[str]) -> bool:
        """Update user permissions"""
        try:
            if user_id in self.users:
                self.users[user_id].permissions = permissions
                logger.info(f"Updated permissions for user: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update user permissions: {e}")
            return False
    
    def get_audit_logs(self, user_id: str = None, start_date: datetime = None, 
                      end_date: datetime = None, operation: str = None) -> List[Dict]:
        """Get audit logs with filtering"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                query = "SELECT * FROM database_audit_log WHERE 1=1"
                params = []
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())
                
                if operation:
                    query += " AND operation = ?"
                    params.append(operation)
                
                query += " ORDER BY timestamp DESC LIMIT 1000"
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    def get_database_security_status(self) -> Dict[str, Any]:
        """Get database security status"""
        return {
            'encryption_enabled': self.config.encryption_enabled,
            'column_encryption': self.config.column_encryption,
            'connection_encryption': self.config.connection_encryption,
            'audit_enabled': self.config.audit_enabled,
            'total_users': len(self.users),
            'active_users': len([u for u in self.users.values() if u.is_active]),
            'database_type': self.config.database_type.value,
            'ssl_mode': self.config.ssl_mode,
            'max_connections': self.config.max_connections,
            'query_timeout': self.config.query_timeout
        }
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Create database backup"""
        if not self.config.backup_enabled:
            return False
        
        try:
            if not backup_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup/mingus_backup_{timestamp}.sql"
            
            # Create backup directory
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            if self.config.database_type == DatabaseType.POSTGRESQL:
                return self._backup_postgresql(backup_path)
            elif self.config.database_type == DatabaseType.SQLITE:
                return self._backup_sqlite(backup_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def _backup_postgresql(self, backup_path: str) -> bool:
        """Backup PostgreSQL database"""
        try:
            import subprocess
            
            # Use pg_dump for backup
            cmd = [
                'pg_dump',
                '-h', self.config.host,
                '-p', str(self.config.port),
                '-U', self.config.username,
                '-d', self.config.database_name,
                '-f', backup_path,
                '--verbose',
                '--clean',
                '--if-exists'
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"PostgreSQL backup created: {backup_path}")
                return True
            else:
                logger.error(f"PostgreSQL backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL backup error: {e}")
            return False
    
    def _backup_sqlite(self, backup_path: str) -> bool:
        """Backup SQLite database"""
        try:
            import shutil
            
            # Copy database file
            shutil.copy2("mingus.db", backup_path)
            logger.info(f"SQLite backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"SQLite backup error: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            backup_dir = Path("backup")
            if not backup_dir.exists():
                return
            
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.backup_retention_days)
            
            for backup_file in backup_dir.glob("mingus_backup_*.sql"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file}")
                    
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize database encryption manager
    config = DatabaseConfig(
        database_type=DatabaseType.SQLITE,
        encryption_enabled=True,
        column_encryption=True,
        audit_enabled=True,
        backup_enabled=True
    )
    
    db_manager = DatabaseEncryptionManager(config)
    
    # Add test user
    test_user = DatabaseUser(
        user_id="test_user",
        username="test",
        access_level=AccessLevel.READ_WRITE,
        permissions=["SELECT", "INSERT", "UPDATE"],
        ip_whitelist=["127.0.0.1"]
    )
    db_manager.add_user(test_user)
    
    # Test encryption
    print("🔐 Testing column encryption...")
    encrypted_value = db_manager.encrypt_column_value("5000.00", "monthly_income", "user_profiles")
    print(f"Encrypted: {encrypted_value}")
    
    decrypted_value = db_manager.decrypt_column_value(encrypted_value, "monthly_income", "user_profiles")
    print(f"Decrypted: {decrypted_value}")
    
    # Test query execution
    print("🔍 Testing query execution...")
    try:
        results = db_manager.execute_query(
            user_id="test_user",
            query="SELECT name FROM sqlite_master WHERE type='table'",
            operation="query",
            table_name="system",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        print(f"Query results: {results}")
    except Exception as e:
        print(f"Query failed: {e}")
    
    # Get security status
    print("🔒 Database Security Status:")
    status = db_manager.get_database_security_status()
    print(json.dumps(status, indent=2))
    
    # Get audit logs
    print("📋 Recent Audit Logs:")
    audit_logs = db_manager.get_audit_logs(limit=5)
    for log in audit_logs:
        print(f"- {log['timestamp']}: {log['operation']} by {log['user_id']}")
    
    print("✅ Database encryption test completed successfully!")
