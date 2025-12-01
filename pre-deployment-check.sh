#!/bin/bash
# Quick Deployment Checklist for Battery RUL Monitoring System
# Run this to verify everything is ready before deployment

echo "=================================="
echo "🔍 PRE-DEPLOYMENT CHECKLIST"
echo "=================================="
echo ""

cd /teamspace/studios/this_studio/NT/RUL_prediction

# 1. Check training data exists
echo "1. Checking training data..."
if [ -f "output/training_dataset/battery.csv" ]; then
    BATTERY_COUNT=$(wc -l < output/training_dataset/battery.csv)
    echo "   ✅ Training data exists: $BATTERY_COUNT batteries"
else
    echo "   ❌ Training data not found"
    exit 1
fi

# 2. Check backend files
echo ""
echo "2. Checking backend files..."
REQUIRED_FILES=(
    "backend/src/main.py"
    "backend/requirements.txt"
    "backend/alembic.ini"
    "backend/Procfile"
    "backend/railway.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# 3. Check Railway CLI
echo ""
echo "3. Checking Railway CLI..."
if command -v railway &> /dev/null; then
    echo "   ✅ Railway CLI installed"
    railway whoami 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ Logged in to Railway"
    else
        echo "   ⚠️  Not logged in. Run: railway login --browserless"
    fi
else
    echo "   ❌ Railway CLI not installed"
    echo "      Install: npm install -g @railway/cli"
    exit 1
fi

# 4. Check documentation
echo ""
echo "4. Checking documentation..."
DOCS=(
    "API_REFERENCE.md"
    "PROJECT_STATUS.md"
    "DEPLOYMENT.md"
    "SESSION_COMPLETE.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✅ $doc"
    else
        echo "   ⚠️  Missing: $doc"
    fi
done

# 5. Check scripts
echo ""
echo "5. Checking utility scripts..."
if [ -f "backend/scripts/load_training_data.py" ] && [ -f "backend/scripts/create_admin.py" ]; then
    echo "   ✅ Data loader script"
    echo "   ✅ Admin creator script"
else
    echo "   ❌ Missing utility scripts"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ ALL CHECKS PASSED!"
echo "=================================="
echo ""
echo "📋 READY TO DEPLOY"
echo ""
echo "Next steps:"
echo ""
echo "1. Deploy to Railway:"
echo "   cd backend"
echo "   railway link cee81f00-c537-4e64-95bb-102fd766e653"
echo "   railway variables set JWT_SECRET_KEY=\$(openssl rand -hex 32)"
echo "   railway variables set ENVIRONMENT=production"
echo "   railway up"
echo ""
echo "2. Setup database:"
echo "   railway run alembic upgrade head"
echo ""
echo "3. Create admin user:"
echo "   railway run python scripts/create_admin.py"
echo ""
echo "4. Test API:"
echo "   curl \$(railway domain)/health"
echo ""
echo "5. View logs:"
echo "   railway logs"
echo ""
echo "📖 Full documentation: See DEPLOYMENT.md"
echo ""
