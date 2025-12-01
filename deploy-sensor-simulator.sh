#!/bin/bash
# Deploy Sensor Simulator to Railway
# Run from project root

set -e

echo "=========================================="
echo "  Sensor Simulator Railway Deployment"
echo "=========================================="
echo ""

# Change to sensor-simulator directory
cd sensor-simulator

echo "✓ Changed to sensor-simulator directory"
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
echo "📦 Creating sensor-simulator service..."
railway add || echo "Service may already exist, continuing..."
echo ""

# Deploy
echo "🚀 Deploying sensor-simulator..."
railway up --service sensor-simulator

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Set PORT variable: railway variables --set PORT=8003 --service sensor-simulator"
echo "2. Check logs: railway logs --service sensor-simulator"
echo "3. Get URL: railway domain --service sensor-simulator"
echo ""
