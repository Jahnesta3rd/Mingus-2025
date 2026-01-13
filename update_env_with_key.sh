#!/bin/bash
# Update .env file with encryption key from venv

cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# Activate venv and generate key
source venv/bin/activate
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

echo "Generated encryption key: ${ENCRYPTION_KEY:0:20}..."

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "Creating .env from env.example..."
        cp env.example .env
    else
        echo "Error: .env not found and env.example not available"
        exit 1
    fi
fi

# Update or add ENCRYPTION_KEY
if grep -q "^ENCRYPTION_KEY=" .env; then
    # Update existing key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env
    else
        # Linux
        sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env
    fi
    echo "✅ Updated ENCRYPTION_KEY in .env"
else
    # Add new key after Security Configuration section
    if grep -q "# Security Configuration" .env; then
        # Insert after CSRF_SECRET_KEY line
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "/^CSRF_SECRET_KEY=/a\\
ENCRYPTION_KEY=$ENCRYPTION_KEY
" .env
        else
            # Linux
            sed -i "/^CSRF_SECRET_KEY=/a ENCRYPTION_KEY=$ENCRYPTION_KEY" .env
        fi
        echo "✅ Added ENCRYPTION_KEY to .env"
    else
        # Just append
        echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
        echo "✅ Added ENCRYPTION_KEY to end of .env"
    fi
fi

echo ""
echo "✅ Encryption key has been set in .env file"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - Keep this key secure and backed up"
echo "   - Never commit .env to version control"
echo "   - Use the same key across all environments"
echo ""
