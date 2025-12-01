#!/bin/bash
# Deploy Frontend to Railway
# Run from project root

set -e

echo "=========================================="
echo "  Frontend Railway Deployment"
echo "=========================================="
echo ""

# Change to frontend directory
cd frontend

echo "✓ Changed to frontend directory"
echo ""

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install with:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

echo "✓ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "⚠️  Not logged in to Railway. Logging in..."
    railway login
fi

echo "✓ Railway authentication verified"
echo ""

# Check Railway project link
echo "📋 Current Railway status:"
railway status
echo ""

# Create service (will fail if already exists, that's OK)
echo "📦 Creating frontend service..."
railway add || echo "Service may already exist, continuing..."
echo ""

# Set environment variables
echo "🔧 Setting environment variables..."
read -p "Backend API URL (default: https://backend-production-6266.up.railway.app): " BACKEND_URL
BACKEND_URL=${BACKEND_URL:-https://backend-production-6266.up.railway.app}

read -p "Sensor Simulator URL (enter when deployed): " SIMULATOR_URL
SIMULATOR_URL=${SIMULATOR_URL:-http://localhost:8003}

railway variables --set VITE_API_URL=$BACKEND_URL --service frontend
railway variables --set VITE_SIMULATOR_URL=$SIMULATOR_URL --service frontend

echo "✓ Environment variables set"
echo ""

# Deploy
echo "🚀 Deploying frontend..."
railway up --service frontend

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Check logs: railway logs --service frontend"
echo "2. Get URL: railway domain --service frontend"
echo "3. Update backend CORS to allow frontend URL"
echo ""
