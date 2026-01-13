#!/bin/bash
# Complete Migration Setup Script
# Sets up encryption keys, installs dependencies, and prepares for migration

set -e  # Exit on error

echo "🔐 Complete Encryption Migration Setup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Install dependencies
echo -e "${GREEN}Step 1: Installing dependencies...${NC}"
if command -v pip3 &> /dev/null; then
    pip3 install bcrypt==4.0.1 cryptography
    echo "✅ Dependencies installed"
else
    echo -e "${RED}❌ pip3 not found. Please install Python dependencies manually.${NC}"
    exit 1
fi

# Step 2: Generate and set encryption key
echo ""
echo -e "${GREEN}Step 2: Setting up encryption key...${NC}"
if [ -f "setup_encryption_key.py" ]; then
    python3 setup_encryption_key.py
    echo "✅ Encryption key setup complete"
else
    echo -e "${YELLOW}⚠️  setup_encryption_key.py not found. Generating key manually...${NC}"
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo ""
    echo -e "${YELLOW}Please add this to your .env file:${NC}"
    echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
    echo ""
fi

# Step 3: Verify .env file exists
echo ""
echo -e "${GREEN}Step 3: Verifying .env file...${NC}"
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "Creating .env from env.example..."
        cp env.example .env
        echo "✅ .env file created"
        echo -e "${YELLOW}⚠️  Please update .env with your actual values${NC}"
    else
        echo -e "${RED}❌ .env file not found and env.example not available${NC}"
        exit 1
    fi
else
    echo "✅ .env file exists"
fi

# Step 4: Check if ENCRYPTION_KEY is set
echo ""
echo -e "${GREEN}Step 4: Verifying ENCRYPTION_KEY...${NC}"
if grep -q "ENCRYPTION_KEY=" .env 2>/dev/null; then
    ENCRYPTION_KEY_VALUE=$(grep "ENCRYPTION_KEY=" .env | cut -d'=' -f2)
    if [ "$ENCRYPTION_KEY_VALUE" != "your-encryption-key-change-in-production" ] && [ -n "$ENCRYPTION_KEY_VALUE" ]; then
        echo "✅ ENCRYPTION_KEY is set in .env"
    else
        echo -e "${YELLOW}⚠️  ENCRYPTION_KEY needs to be updated in .env${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  ENCRYPTION_KEY not found in .env${NC}"
fi

# Step 5: Test encryption service
echo ""
echo -e "${GREEN}Step 5: Testing encryption service...${NC}"
if python3 -c "from backend.utils.encryption import EncryptionService; import os; from cryptography.fernet import Fernet; os.environ['ENCRYPTION_KEY'] = Fernet.generate_key().decode(); s = EncryptionService(); e = s.encrypt('test'); d = s.decrypt(e); assert d == 'test'; print('✅ Encryption service works')" 2>/dev/null; then
    echo "✅ Encryption service test passed"
else
    echo -e "${RED}❌ Encryption service test failed${NC}"
fi

# Step 6: Test password hashing
echo ""
echo -e "${GREEN}Step 6: Testing password hashing...${NC}"
if python3 -c "from backend.utils.password import hash_password, check_password; h = hash_password('test'); assert check_password('test', h); print('✅ Password hashing works')" 2>/dev/null; then
    echo "✅ Password hashing test passed"
else
    echo -e "${RED}❌ Password hashing test failed${NC}"
fi

# Summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Run migration scripts:"
echo "   - python3 migrate_encrypted_data.py (for data migration)"
echo "   - python3 migrate_password_hashes.py (for password migration)"
echo "3. Test your application"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "   - Keep ENCRYPTION_KEY secure and backed up"
echo "   - Never commit .env to version control"
echo "   - Use the same key across all environments"
echo ""
