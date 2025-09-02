# Mingus Flask Application - Encryption System

## Overview

The Mingus Flask application implements an enterprise-grade encryption system that provides field-level encryption for sensitive financial data, PII, and session information. The system features automatic key rotation, multi-backend storage support, and comprehensive audit logging.

## Architecture

### Core Components

1. **CryptoConfigManager** (`backend/security/crypto_config.py`)
   - Manages encryption configuration and environment variables
   - Handles key rotation policies and performance settings
   - Supports multiple encryption algorithms and modes

2. **KeyManager** (`backend/security/key_manager.py`)
   - Generates, stores, and manages encryption keys
   - Supports multiple storage backends (file, Redis, Vault, AWS KMS, Azure KV, GCP KMS)
   - Handles key rotation and lifecycle management

3. **EncryptionService** (`backend/security/encryption_service.py`)
   - Provides encryption/decryption services for different data types
   - Supports field-level, bulk, session, and cache encryption
   - Integrates with database models for seamless encryption

4. **KeyRotationTasks** (`backend/tasks/key_rotation.py`)
   - Celery tasks for automated key rotation
   - Background data re-encryption during key rotation
   - Monitoring and reporting capabilities

## Features

### 🔐 Encryption Capabilities
- **Field-level encryption** for sensitive financial data
- **Bulk data encryption** with compression support
- **Session data encryption** for Redis storage
- **Cache encryption** for sensitive cached data
- **Database field encryption** with automatic key type detection

### 🔑 Key Management
- **Automatic key rotation** based on configurable policies
- **Multiple key types** (financial data, PII, sessions, API keys, audit logs)
- **Key versioning** and backwards compatibility
- **Key revocation** and compromise handling
- **Multi-backend storage** support

### 🚀 Performance & Security
- **Hardware acceleration** support
- **Configurable performance modes** (security, balanced, performance)
- **Compression** for large data sets
- **Audit logging** for compliance
- **PCI DSS, SOX, GDPR** compliance ready

## Installation & Setup

### 1. Environment Variables

Set the following environment variables:

```bash
# Required
export ENCRYPTION_MASTER_KEY="your_base64_encoded_master_key"
export ENCRYPTION_KEY_ID="your_key_id"
export ENCRYPTION_KEY_VERSION="1.0"

# Optional - Key Storage Backend
export ENCRYPTION_KEY_STORAGE_BACKEND="file"  # file, redis, vault, aws_kms, azure_kv, gcp_kms

# File Storage (default)
export ENCRYPTION_KEY_STORAGE_PATH="/path/to/keys"

# Redis Storage
export ENCRYPTION_REDIS_URL="redis://localhost:6379/0"

# HashiCorp Vault
export ENCRYPTION_VAULT_URL="https://vault.example.com"
export ENCRYPTION_VAULT_TOKEN="your_vault_token"

# AWS KMS
export ENCRYPTION_AWS_REGION="us-east-1"
export ENCRYPTION_AWS_ACCESS_KEY_ID="your_access_key"
export ENCRYPTION_AWS_SECRET_ACCESS_KEY="your_secret_key"

# Azure Key Vault
export ENCRYPTION_AZURE_TENANT_ID="your_tenant_id"
export ENCRYPTION_AZURE_CLIENT_ID="your_client_id"
export ENCRYPTION_AZURE_CLIENT_SECRET="your_client_secret"

# Google Cloud KMS
export ENCRYPTION_GCP_PROJECT_ID="your_project_id"
export ENCRYPTION_GCP_LOCATION="global"
export ENCRYPTION_GCP_KEYRING="mingus-encryption"
```

### 2. Generate Master Key

```python
from cryptography.fernet import Fernet
import base64

# Generate a new master key
master_key = Fernet.generate_key()
encoded_key = base64.b64encode(master_key).decode()

print(f"ENCRYPTION_MASTER_KEY={encoded_key}")
```

### 3. Database Migration

Run the encryption migration to add encrypted columns:

```bash
# Using Alembic
alembic upgrade head

# Or manually run the migration
python -m backend.migrations.add_encryption_fields
```

### 4. Initialize Encryption System

```python
from backend.security.key_manager import get_key_manager
from backend.security.encryption_service import get_encryption_service

# Initialize key manager
key_manager = get_key_manager()

# Initialize encryption service
encryption_service = get_encryption_service()

# Generate initial keys
for key_type in ['financial_data', 'pii', 'session', 'api_keys', 'audit_logs']:
    key_manager.generate_key(key_type)
```

## Usage Examples

### Basic Field Encryption

```python
from backend.security.encryption_service import get_encryption_service
from backend.security.crypto_config import KeyType

encryption_service = get_encryption_service()

# Encrypt financial data
monthly_income = 75000.0
encrypted_income = encryption_service.encrypt_field(
    monthly_income, 
    KeyType.FINANCIAL_DATA
)

# Decrypt financial data
decrypted_income = encryption_service.decrypt_field(
    encrypted_income, 
    KeyType.FINANCIAL_DATA
)

assert decrypted_income == monthly_income
```

### Database Model Integration

```python
from backend.models.user import User
from backend.security.encryption_service import get_encryption_service

# Create user with encrypted data
user = User()
user.monthly_income_encrypted = 50000.0  # Automatically encrypted
user.current_savings_encrypted = 25000.0
user.ssn_encrypted = "123-45-6789"

# Save to database
db.session.add(user)
db.session.commit()

# Retrieve and decrypt
retrieved_user = User.query.get(user.id)
print(f"Monthly Income: ${retrieved_user.monthly_income_encrypted}")
print(f"SSN: {retrieved_user.ssn_encrypted}")
```

### Session Data Encryption

```python
from backend.security.encryption_service import get_encryption_service

encryption_service = get_encryption_service()

# Encrypt session data
session_data = {
    'user_id': 123,
    'permissions': ['read', 'write'],
    'last_activity': '2024-01-15T10:30:00Z'
}

encrypted_session = encryption_service.encrypt_session_data(session_data)

# Store in Redis
redis_client.set(f"session:{session_id}", encrypted_session)

# Retrieve and decrypt
stored_session = redis_client.get(f"session:{session_id}")
decrypted_session = encryption_service.decrypt_session_data(stored_session)
```

### Bulk Data Encryption

```python
from backend.security.encryption_service import get_encryption_service

encryption_service = get_encryption_service()

# Encrypt large dataset
financial_report = b"Large financial report data..."
encrypted_report = encryption_service.encrypt_bulk_data(
    financial_report, 
    KeyType.FINANCIAL_DATA
)

# Store encrypted data
with open('encrypted_report.bin', 'wb') as f:
    f.write(encrypted_report.encrypted_data)

# Decrypt when needed
with open('encrypted_report.bin', 'rb') as f:
    encrypted_data = f.read()

# Reconstruct EncryptedData object
encrypted_report_obj = EncryptedData(
    encrypted_data=encrypted_data,
    key_id=encrypted_report.key_id,
    algorithm=encrypted_report.algorithm,
    iv=encrypted_report.iv,
    tag=encrypted_report.tag
)

decrypted_report = encryption_service.decrypt_bulk_data(encrypted_report_obj)
```

## Key Rotation

### Automatic Rotation

The system automatically rotates keys based on configured policies:

```python
from backend.security.key_manager import get_key_manager
from backend.security.crypto_config import KeyType

key_manager = get_key_manager()

# Check if rotation is needed
financial_key = key_manager.get_active_key(KeyType.FINANCIAL_DATA)
if financial_key:
    days_until_expiry = (financial_key.expires_at - datetime.utcnow()).days
    print(f"Financial key expires in {days_until_expiry} days")

# Force rotation
new_key = key_manager.rotate_key(KeyType.FINANCIAL_DATA, force=True)
print(f"New key generated: {new_key.key_id}")
```

### Manual Rotation

```python
from backend.tasks.key_rotation import rotate_key_manual

# Manual key rotation
result = rotate_key_manual.delay('financial_data', force=True)
print(f"Rotation result: {result.get()}")
```

### Data Re-encryption

During key rotation, existing data is automatically re-encrypted:

```python
from backend.tasks.key_rotation import reencrypt_data_with_new_key

# Re-encrypt data with new key
result = reencrypt_data_with_new_key.delay(
    'financial_data', 
    'old_key_id', 
    batch_size=1000
)

print(f"Re-encryption progress: {result.get()}")
```

## Configuration

### Encryption Configuration

The system can be configured via `config/encryption.json`:

```json
{
  "algorithm": "AES_256_GCM",
  "key_size_bits": 256,
  "performance_mode": "balanced",
  "compression_enabled": true,
  "rotation_policies": [
    {
      "key_type": "financial_data",
      "rotation_interval_days": 90,
      "max_key_age_days": 365,
      "grace_period_days": 30,
      "auto_rotation": true,
      "batch_size": 500
    }
  ]
}
```

### Performance Modes

- **Security**: Maximum security, slower performance
- **Balanced**: Good balance of security and performance
- **Performance**: Maximum performance, reduced security

### Key Rotation Policies

- **financial_data**: 90-day rotation, 365-day max age
- **pii**: 180-day rotation, 730-day max age
- **session**: 30-day rotation, 90-day max age
- **api_keys**: 90-day rotation, 365-day max age
- **audit_logs**: 365-day rotation, 1825-day max age

## Monitoring & Maintenance

### Health Checks

```python
from backend.security.key_manager import get_key_manager
from backend.security.encryption_service import get_encryption_service

# Check key health
key_manager = get_key_manager()
key_stats = key_manager.get_key_statistics()
print(f"Total keys: {key_stats['total_keys']}")
print(f"Keys needing rotation: {len(key_stats['rotation_needed'])}")

# Check encryption service health
encryption_service = get_encryption_service()
encryption_stats = encryption_service.get_encryption_stats()
print(f"Service status: {encryption_stats['encryption_service']}")
```

### Scheduled Tasks

Configure Celery to run key rotation tasks:

```python
# Celery beat schedule
CELERYBEAT_SCHEDULE = {
    'rotate-keys-daily': {
        'task': 'backend.tasks.key_rotation.rotate_keys_scheduled',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'options': {'queue': 'encryption'}
    },
    'cleanup-expired-keys': {
        'task': 'backend.tasks.key_rotation.cleanup_expired_keys',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # 3 AM Sundays
        'options': {'queue': 'encryption'}
    }
}
```

### Logging

The system provides comprehensive logging:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('encryption')

# Monitor key operations
logger.info("Key rotation completed successfully")
logger.warning("Key expiration approaching")
logger.error("Encryption operation failed")
```

## Security Considerations

### Master Key Security
- Store master key securely (environment variables, secret management)
- Rotate master key periodically
- Use hardware security modules (HSM) in production

### Key Storage
- File storage: Secure file permissions, encrypted at rest
- Redis: Enable Redis encryption, secure network access
- Cloud KMS: Use IAM policies, enable audit logging

### Data Protection
- Encrypt sensitive data at rest and in transit
- Implement proper access controls
- Regular security audits and penetration testing

### Compliance
- PCI DSS: Encrypt cardholder data
- SOX: Protect financial data integrity
- GDPR: Encrypt personal data
- HIPAA: Encrypt protected health information

## Troubleshooting

### Common Issues

1. **Key Not Found**
   ```python
   # Check key storage
   key_manager = get_key_manager()
   keys = key_manager.list_keys()
   print(f"Available keys: {[k.key_id for k in keys]}")
   ```

2. **Decryption Failed**
   ```python
   # Check key status
   key = key_manager.get_key(key_id)
   print(f"Key status: {key.status}")
   print(f"Key expiry: {key.expires_at}")
   ```

3. **Performance Issues**
   ```python
   # Check performance mode
   config = get_crypto_config()
   print(f"Performance mode: {config.get_config().performance_mode}")
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('backend.security').setLevel(logging.DEBUG)
```

## Testing

### Run Tests

```bash
# Run all encryption tests
pytest tests/test_encryption.py -v

# Run specific test categories
pytest tests/test_encryption.py::TestCryptoConfig -v
pytest tests/test_encryption.py::TestKeyManager -v
pytest tests/test_encryption.py::TestEncryptionService -v

# Run performance tests
pytest tests/test_encryption.py::TestPerformance -v

# Run integration tests
pytest tests/test_encryption.py::TestEncryptionIntegration -v
```

### Performance Benchmarks

```bash
# Run performance benchmarks
python tests/test_encryption.py
```

## API Reference

### KeyManager

```python
class KeyManager:
    def generate_key(self, key_type: KeyType, key_size: Optional[int] = None) -> EncryptionKey
    def get_active_key(self, key_type: KeyType) -> Optional[EncryptionKey]
    def rotate_key(self, key_type: KeyType, force: bool = False) -> EncryptionKey
    def revoke_key(self, key_id: str, reason: str = "Manual revocation") -> None
    def list_keys(self, key_type: Optional[KeyType] = None, status: Optional[KeyStatus] = None) -> List[EncryptionKey]
    def cleanup_expired_keys(self) -> int
    def get_key_statistics(self) -> Dict[str, Any]
```

### EncryptionService

```python
class EncryptionService:
    def encrypt_field(self, value: Any, key_type: KeyType = KeyType.FINANCIAL_DATA) -> str
    def decrypt_field(self, encrypted_value: str, key_type: KeyType = KeyType.FINANCIAL_DATA) -> Any
    def encrypt_bulk_data(self, data: bytes, key_type: KeyType = KeyType.FINANCIAL_DATA) -> EncryptedData
    def decrypt_bulk_data(self, encrypted_data: EncryptedData) -> bytes
    def encrypt_session_data(self, session_data: Dict[str, Any]) -> str
    def decrypt_session_data(self, encrypted_session: str) -> Dict[str, Any]
    def encrypt_cache_data(self, cache_key: str, cache_value: Any, ttl: int = 3600) -> Tuple[str, str]
    def decrypt_cache_data(self, encrypted_key: str, encrypted_value: str) -> Tuple[str, Any]
```

### CryptoConfigManager

```python
class CryptoConfigManager:
    def get_config(self) -> EncryptionConfig
    def get_rotation_policy(self, key_type: KeyType) -> KeyRotationPolicy
    def update_config(self, new_config: EncryptionConfig) -> None
    def validate_environment(self) -> List[str]
    def get_performance_settings(self) -> Dict[str, Any]
```

## Support & Contributing

### Getting Help

- Check the logs for error messages
- Review configuration files
- Run health checks and diagnostics
- Consult the test suite for examples

### Contributing

1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation
4. Ensure security best practices
5. Test with different backends

### Reporting Issues

Include the following information:
- Error messages and stack traces
- Configuration details
- Environment information
- Steps to reproduce
- Expected vs actual behavior

## License

This encryption system is part of the Mingus Flask application and follows the same licensing terms.

---

**Note**: This encryption system is designed for production use but should be thoroughly tested in your specific environment before deployment. Always follow security best practices and compliance requirements for your industry.
