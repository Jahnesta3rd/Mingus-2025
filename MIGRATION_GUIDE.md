# 🔄 Complete Migration Guide

**Date:** January 8, 2026  
**Purpose:** Complete setup and migration from insecure encryption to secure encryption

---

## 📋 Overview

This guide walks you through:
1. ✅ Installing dependencies (bcrypt)
2. ✅ Setting up encryption keys
3. ✅ Migrating encrypted data
4. ✅ Migrating password hashes

---

## Step 1: Install Dependencies

### Install bcrypt

```bash
# Using pip
pip install bcrypt==4.0.1

# Or using pip3
pip3 install bcrypt==4.0.1

# Or from requirements.txt
pip install -r requirements.txt
```

### Verify Installation

```bash
python3 -c "import bcrypt; print('✅ bcrypt installed')"
python3 -c "from cryptography.fernet import Fernet; print('✅ cryptography installed')"
```

---

## Step 2: Set Up Encryption Key

### Option A: Automated Setup (Recommended)

```bash
# Run the setup script
python3 setup_encryption_key.py
```

This script will:
- Generate a new Fernet encryption key
- Add it to your `.env` file
- Provide instructions for backup

### Option B: Manual Setup

1. **Generate a key:**
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Add to `.env` file:**
   ```bash
   # Open .env file
   nano .env  # or use your preferred editor
   
   # Add or update this line:
   ENCRYPTION_KEY=your-generated-key-here
   ```

3. **Verify:**
   ```bash
   # Check that key is set
   grep ENCRYPTION_KEY .env
   ```

### Option C: Use Complete Setup Script

```bash
# Run the complete setup script
./complete_migration_setup.sh
```

This script will:
- Install dependencies
- Generate and set encryption key
- Verify configuration
- Test encryption service

---

## Step 3: Verify Encryption Service

### Test Encryption

```python
from backend.utils.encryption import EncryptionService
import os
from cryptography.fernet import Fernet

# Set key (or load from .env)
os.environ['ENCRYPTION_KEY'] = Fernet.generate_key().decode()

# Test encryption
service = EncryptionService()
data = "sensitive test data"
encrypted = service.encrypt(data)
decrypted = service.decrypt(encrypted)

print(f"Original: {data}")
print(f"Encrypted: {encrypted[:50]}...")
print(f"Decrypted: {decrypted}")
assert decrypted == data
print("✅ Encryption service works!")
```

### Test Password Hashing

```python
from backend.utils.password import hash_password, check_password

# Hash password
hashed = hash_password("test_password_123")
print(f"Hashed: {hashed[:30]}...")

# Verify password
assert check_password("test_password_123", hashed) == True
assert check_password("wrong_password", hashed) == False
print("✅ Password hashing works!")
```

---

## Step 4: Migrate Encrypted Data

### Understanding the Problem

**Old "Encryption":**
- Used base64 encoding (NOT real encryption)
- Format: `encrypted_<base64_encoded_data>`
- Can be decoded by anyone
- No security provided

**New Encryption:**
- Uses Fernet (AES-128 with HMAC)
- Authenticated encryption
- Cannot be decoded without key
- Proper security

### Migration Process

1. **Identify Data to Migrate:**
   ```bash
   # Run migration utility to scan for old encryption
   python3 migrate_encrypted_data.py
   ```

2. **Manual Migration Example:**
   ```python
   from backend.utils.encryption import EncryptionService
   from migrate_encrypted_data import DataMigration
   
   migration = DataMigration()
   
   # Old encrypted data (base64)
   old_data = "encrypted_" + base64.b64encode("sensitive data".encode()).decode()
   
   # Migrate to new encryption
   new_data = migration.migrate_string(old_data)
   
   # Update in database
   # user.sensitive_field = new_data
   # db.session.commit()
   ```

3. **Database Migration:**
   - Identify all tables/collections with encrypted fields
   - For each record:
     - Check if data uses old format
     - Decode old "encryption" (it's just base64)
     - Encrypt with new service
     - Update database
   - Verify migrated data can be decrypted

### Migration Checklist

- [ ] Identify all encrypted data locations
- [ ] Backup database before migration
- [ ] Test migration on sample data
- [ ] Run migration script
- [ ] Verify migrated data can be decrypted
- [ ] Remove old encrypted data after verification
- [ ] Update application code to use new encryption

---

## Step 5: Migrate Password Hashes

### Understanding the Problem

**Old Password Hashing:**
- Used SHA256 (insecure for passwords)
- Fast hash (vulnerable to brute force)
- No automatic salting
- Format: 64 hex characters

**New Password Hashing:**
- Uses bcrypt (secure for passwords)
- Slow hash (resists brute force)
- Automatic salting
- Format: 60 characters starting with `$2b$`

### Migration Strategy

**⚠️ IMPORTANT:** SHA256 hashes **cannot** be converted to bcrypt. Users must either:
1. Reset their passwords (creates bcrypt hash)
2. Migrate on next login (verify old hash, create new hash)

### Option A: Migrate on Login (Recommended)

**Best User Experience**

```python
from backend.utils.password import hash_password, check_password
from migrate_password_hashes import PasswordMigration

def login_user(email: str, password: str):
    """Login with automatic password migration"""
    migration = PasswordMigration()
    
    # Get user
    user = get_user_by_email(email)
    if not user:
        return {'error': 'Invalid credentials'}
    
    stored_hash = user.password_hash
    
    # Check if using old SHA256 hash
    if migration.is_sha256_hash(stored_hash):
        # Verify against old hash
        if migration.verify_sha256_password(password, stored_hash):
            # Migrate to bcrypt
            new_hash = hash_password(password)
            user.password_hash = new_hash
            db.session.commit()
            logger.info(f"Migrated password for {email}")
        else:
            return {'error': 'Invalid password'}
    else:
        # Use new bcrypt verification
        if not check_password(password, stored_hash):
            return {'error': 'Invalid password'}
    
    # Create session and return
    return {'success': True, 'user_id': user.id}
```

### Option B: Force Password Reset

**Faster Migration, Requires User Action**

1. Mark all SHA256 hashes as needing reset
2. Send password reset emails to all users
3. Users reset passwords (creates bcrypt hashes)
4. Remove old SHA256 hashes after reset period

### Migration Checklist

- [ ] Identify all password hash locations
- [ ] Backup database before migration
- [ ] Implement login migration or reset flow
- [ ] Test migration with sample users
- [ ] Monitor migration progress
- [ ] Remove old SHA256 hashes after migration

---

## Step 6: Update Application Code

### Update Encryption Usage

**Before:**
```python
from backend.utils.encryption import EncryptionService

# Old code (worked with base64)
service = EncryptionService()
encrypted = service.encrypt(data)
```

**After:**
```python
from backend.utils.encryption import EncryptionService

# New code (requires ENCRYPTION_KEY)
# ENCRYPTION_KEY must be set in environment
service = EncryptionService()  # Gets key from ENCRYPTION_KEY env var
encrypted = service.encrypt(data)
```

### Update Password Hashing

**Before:**
```python
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
```

**After:**
```python
from backend.utils.password import hash_password, check_password

# Hash password
hashed = hash_password(password)

# Verify password
is_valid = check_password(password, hashed)
```

---

## Step 7: Testing

### Run Security Tests

```bash
# Run encryption tests
python3 -m pytest tests/security/test_daily_outlook_security.py::TestDataEncryptionAndProtection -v

# Run password hashing tests
python3 -m pytest tests/security/test_daily_outlook_security.py::TestDataEncryptionAndProtection::test_password_hashing -v
```

### Manual Testing

1. **Test Encryption:**
   - Encrypt test data
   - Verify it's different from original
   - Decrypt and verify it matches

2. **Test Password Hashing:**
   - Hash a test password
   - Verify it's different from original
   - Verify correct password works
   - Verify wrong password fails

3. **Test Migration:**
   - Create old format data
   - Migrate to new format
   - Verify it can be decrypted

---

## Step 8: Production Deployment

### Pre-Deployment Checklist

- [ ] ENCRYPTION_KEY set in production environment
- [ ] bcrypt installed in production
- [ ] All encrypted data migrated
- [ ] All password hashes migrated (or migration plan in place)
- [ ] Security tests passing
- [ ] Backup of encryption key stored securely
- [ ] Documentation updated

### Environment Variables

**Required in Production:**
```bash
ENCRYPTION_KEY=<your-production-encryption-key>
SECRET_KEY=<your-production-secret-key>
```

**Key Management:**
- Store keys in secure key management service (AWS Secrets Manager, HashiCorp Vault, etc.)
- Never commit keys to version control
- Use different keys for dev/staging/production
- Rotate keys periodically

### Backup Encryption Key

**⚠️ CRITICAL:** If you lose the encryption key, encrypted data cannot be decrypted!

1. Generate key
2. Store in secure location:
   - Password manager
   - Key management service
   - Encrypted backup
3. Document key location (but not the key itself)
4. Test key recovery process

---

## Troubleshooting

### Encryption Service Errors

**Error: "ENCRYPTION_KEY environment variable is required"**

**Solution:**
```bash
# Set in .env file
echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env

# Or export in shell
export ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
```

### Password Hashing Errors

**Error: "ModuleNotFoundError: No module named 'bcrypt'"**

**Solution:**
```bash
pip install bcrypt==4.0.1
```

### Migration Errors

**Error: "Failed to decrypt data"**

**Possible Causes:**
- Wrong encryption key
- Data corrupted
- Data not actually encrypted (old base64 format)

**Solution:**
- Verify ENCRYPTION_KEY is correct
- Check data format
- Use migration utility to identify old format data

---

## Support

For issues or questions:
1. Check this guide
2. Review `ENCRYPTION_FIXES_COMPLETE.md`
3. Review `DATA_ENCRYPTION_PROTECTION_VERIFICATION_REPORT.md`
4. Check migration utility scripts for examples

---

**Last Updated:** January 8, 2026  
**Status:** ✅ Ready for Migration
