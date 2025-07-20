#!/bin/bash

# Marketing Funnel Integration Script
# This script helps integrate the Ratchet Money marketing funnel into an existing React app

echo "🚀 Marketing Funnel Integration Script"
echo "======================================"

# Check if target directory is provided
if [ -z "$1" ]; then
    echo "Usage: ./integrate-marketing-funnel.sh <path-to-your-main-app>"
    echo "Example: ./integrate-marketing-funnel.sh ../my-main-app"
    exit 1
fi

TARGET_APP="$1"
CURRENT_DIR=$(pwd)

echo "📁 Current directory: $CURRENT_DIR"
echo "🎯 Target app: $TARGET_APP"

# Check if target directory exists
if [ ! -d "$TARGET_APP" ]; then
    echo "❌ Error: Target directory does not exist: $TARGET_APP"
    exit 1
fi

echo ""
echo "📋 Integration Steps:"
echo "===================="

# Step 1: Create marketing funnel directories
echo "1️⃣ Creating marketing funnel directories..."
mkdir -p "$TARGET_APP/src/components/marketing-funnel"
mkdir -p "$TARGET_APP/src/api/marketing-funnel"
mkdir -p "$TARGET_APP/src/types/marketing-funnel"
mkdir -p "$TARGET_APP/src/utils/marketing-funnel"

# Step 2: Copy components
echo "2️⃣ Copying components..."
cp -r "$CURRENT_DIR/src/components/"* "$TARGET_APP/src/components/marketing-funnel/"

# Step 3: Copy API services
echo "3️⃣ Copying API services..."
cp -r "$CURRENT_DIR/src/api/"* "$TARGET_APP/src/api/marketing-funnel/"

# Step 4: Copy types
echo "4️⃣ Copying types..."
cp -r "$CURRENT_DIR/src/types/"* "$TARGET_APP/src/types/marketing-funnel/"

# Step 5: Copy utils
echo "5️⃣ Copying utilities..."
cp -r "$CURRENT_DIR/src/utils/"* "$TARGET_APP/src/utils/marketing-funnel/"

# Step 6: Copy integration guide
echo "6️⃣ Copying integration guide..."
cp "$CURRENT_DIR/INTEGRATION_GUIDE.md" "$TARGET_APP/"

echo ""
echo "✅ Files copied successfully!"
echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Update your main app's router (see INTEGRATION_GUIDE.md)"
echo "2. Add environment variables to your .env file"
echo "3. Update your Supabase client with marketing funnel types"
echo "4. Deploy the database schema to your Supabase project"
echo "5. Test the integration"
echo ""
echo "📖 For detailed instructions, see: $TARGET_APP/INTEGRATION_GUIDE.md"
echo ""
echo "🎉 Integration script completed!" 