#!/bin/bash
# Railway Deployment Script for Battery RUL Monitoring System
# This script guides you through deploying the backend to Railway.com

set -e  # Exit on error

echo "=========================================="
echo "Battery RUL Monitoring - Railway Deployment"
echo "=========================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed"
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI installed"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Not logged in to Railway. Logging in..."
    railway login --browserless
else
    echo "✅ Already logged in to Railway"
fi

echo ""
echo "Step 1: Database Setup"
echo "----------------------------------------"
echo "The PostgreSQL database should already be added."
echo "Checking database connection..."

# Link to database
cd backend

# Check if DATABASE_URL is set
if railway variables | grep -q "DATABASE_URL"; then
    echo "✅ DATABASE_URL is configured"
else
    echo "⚠️  DATABASE_URL not found. Make sure PostgreSQL database is added."
    echo "Run: railway add --database postgres"
    exit 1
fi

echo ""
echo "Step 2: Set Environment Variables"
echo "----------------------------------------"

# Generate JWT secret if not exists
if ! railway variables | grep -q "JWT_SECRET_KEY"; then
    echo "Generating JWT_SECRET_KEY..."
    JWT_SECRET=$(openssl rand -hex 32)
    railway variables --set JWT_SECRET_KEY=$JWT_SECRET
    echo "✅ JWT_SECRET_KEY set"
else
    echo "✅ JWT_SECRET_KEY already set"
fi

# Set other variables
echo "Setting other environment variables..."
railway variables --set ENVIRONMENT=production
railway variables --set LOG_LEVEL=INFO
railway variables --set ENABLE_TELEMETRY_BROADCAST=false
railway variables --set 'CORS_ORIGINS=["*"]'  # Configure properly in production

echo "✅ Environment variables configured"
echo ""

echo "Step 3: Deploy Backend"
echo "----------------------------------------"
echo "Deploying backend service to Railway..."

railway up

echo "✅ Backend deployed"
echo ""

echo "Step 4: Run Database Migrations"
echo "----------------------------------------"
echo "Running Alembic migrations..."

railway run alembic upgrade head

echo "✅ Migrations completed"
echo ""

echo "Step 5: Create Admin User (Optional)"
echo "----------------------------------------"
read -p "Do you want to create an admin user now? (y/n): " create_admin

if [[ $create_admin == "y" || $create_admin == "Y" ]]; then
    read -p "Admin username: " admin_username
    read -p "Admin email: " admin_email
    read -sp "Admin password: " admin_password
    echo ""

    railway run python scripts/create_admin.py \
        --user-id admin \
        --username "$admin_username" \
        --email "$admin_email" \
        --password "$admin_password" \
        --full-name "System Administrator"

    echo "✅ Admin user created"
else
    echo "⚠️  Skipping admin user creation"
    echo "   You can create one later with:"
    echo "   railway run python scripts/create_admin.py"
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""

# Get deployment URL
DEPLOYMENT_URL=$(railway domain)

if [ -n "$DEPLOYMENT_URL" ]; then
    echo "Your API is deployed at:"
    echo "  $DEPLOYMENT_URL"
    echo ""
    echo "API Documentation:"
    echo "  $DEPLOYMENT_URL/api/docs"
    echo ""
    echo "Health Check:"
    echo "  $DEPLOYMENT_URL/health"
    echo ""
else
    echo "⚠️  No custom domain configured yet"
    echo "   Configure one in the Railway dashboard"
    echo "   or use the Railway-generated URL"
fi

echo "Next Steps:"
echo "  1. Test the API: curl $DEPLOYMENT_URL/health"
echo "  2. Login: POST $DEPLOYMENT_URL/api/v1/auth/login"
echo "  3. Load training data: railway run python scripts/load_training_data.py"
echo "  4. Deploy frontend (coming soon)"
echo ""
echo "Railway Dashboard:"
echo "  https://railway.com/project/cee81f00-c537-4e64-95bb-102fd766e653"
echo ""
