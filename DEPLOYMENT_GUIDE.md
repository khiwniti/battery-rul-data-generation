# Complete Deployment Guide
## Battery RUL Prediction System

This guide covers deploying all services to Railway.com in the correct order.

---

## Prerequisites

1. **Railway CLI installed**
   ```bash
   npm install -g @railway/cli
   ```

2. **Railway account and login**
   ```bash
   railway login
   ```

3. **Railway project created**
   - Project: `battery-rul-monitoring`
   - Environment: `production`

---

## Current Deployment Status

| Service | Status | URL |
|---------|--------|-----|
| Backend API | ✅ Deployed | https://backend-production-6266.up.railway.app |
| PostgreSQL Database | ✅ Deployed | Connected to backend |
| Sensor Simulator | ⏳ Ready | Not deployed yet |
| Frontend | ⏳ Ready | Not deployed yet |
| ML Pipeline | 📝 Skeleton | Not ready |

---

## Step 1: Deploy Backend (Already Complete ✅)

The backend is already deployed and operational:

- **URL**: https://backend-production-6266.up.railway.app
- **Health**: `/health` → 200 OK
- **Docs**: `/docs` → Swagger UI
- **Database**: PostgreSQL on Railway (migrations complete)
- **Admin User**: admin / Admin123!

**Test the backend**:
```bash
curl https://backend-production-6266.up.railway.app/health
```

---

## Step 2: Deploy Sensor Simulator

### Option A: Automated Deployment

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction
./deploy-sensor-simulator.sh
```

### Option B: Manual Deployment

```bash
# Navigate to sensor-simulator
cd sensor-simulator

# Link to Railway project
railway link

# Deploy
railway up

# Wait for deployment, then get the URL
railway domain

# Example output: sensor-simulator-production.up.railway.app
```

### Post-Deployment Configuration

After deployment completes:

```bash
# Set PORT variable (if not auto-detected)
railway variables --set PORT=8003

# Check deployment logs
railway logs

# Test health endpoint
curl https://sensor-simulator-production.up.railway.app/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "service": "sensor-simulator",
  "version": "1.0.0"
}
```

### Test Sensor Simulator Endpoints

```bash
# List available scenarios
curl https://sensor-simulator-production.up.railway.app/api/v1/scenarios

# Check simulation status
curl https://sensor-simulator-production.up.railway.app/api/v1/simulation/status

# Start a test simulation
curl -X POST https://sensor-simulator-production.up.railway.app/api/v1/simulation/start \
  -H "Content-Type: application/json" \
  -d '{
    "batteries": [
      {"battery_id": "TEST_BAT001", "profile": "healthy", "initial_soh": 95.0}
    ],
    "interval_seconds": 5
  }'
```

---

## Step 3: Deploy Frontend

### Option A: Automated Deployment

```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction
./deploy-frontend.sh
```

The script will prompt you for:
- Backend API URL (default: https://backend-production-6266.up.railway.app)
- Sensor Simulator URL (enter the URL from Step 2)

### Option B: Manual Deployment

```bash
# Navigate to frontend
cd frontend

# Link to Railway project
railway link

# Set environment variables
railway variables --set VITE_API_URL=https://backend-production-6266.up.railway.app
railway variables --set VITE_SIMULATOR_URL=https://sensor-simulator-production.up.railway.app

# Deploy
railway up

# Wait for deployment, then get the URL
railway domain

# Example output: frontend-production.up.railway.app
```

### Post-Deployment Configuration

After deployment completes:

```bash
# Check deployment logs
railway logs

# Test frontend
# Open in browser: https://frontend-production.up.railway.app
```

---

## Step 4: Update Backend CORS

After frontend is deployed, update the backend to allow requests from the frontend domain.

### Update CORS in Backend

Edit `backend/src/core/config.py`:

```python
# Add frontend URL to CORS origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://frontend-production.up.railway.app",  # Add this
]
```

### Redeploy Backend

```bash
cd backend
railway up
```

---

## Step 5: Verification & Testing

### 1. Backend Health Check
```bash
curl https://backend-production-6266.up.railway.app/health
```

### 2. Sensor Simulator Health Check
```bash
curl https://sensor-simulator-production.up.railway.app/health
```

### 3. Frontend Access
Open browser: https://frontend-production.up.railway.app

**Login Credentials**:
- Username: `admin`
- Password: `Admin123!`

### 4. Test Full Integration

1. **Login** to frontend with admin credentials
2. **Dashboard**: Should load location statistics
3. **Simulator Control Panel**: Navigate to `/simulator`
   - Start a simulation with test batteries
   - Apply scenarios
   - Check real-time status updates
4. **Alerts Page**: Navigate to `/alerts`
   - Should show alert statistics
   - Test filtering and pagination
5. **Battery Detail**: Click on a battery
   - Should show telemetry charts
   - WebSocket should stream real-time data

---

## Environment Variables Summary

### Backend
```bash
DATABASE_URL=postgresql://...  # Provided by Railway PostgreSQL
JWT_SECRET_KEY=<your-secret-key>
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Sensor Simulator
```bash
PORT=8003  # Auto-detected by Railway
```

### Frontend
```bash
VITE_API_URL=https://backend-production-6266.up.railway.app
VITE_SIMULATOR_URL=https://sensor-simulator-production.up.railway.app
```

---

## Monitoring & Troubleshooting

### Check Service Logs

```bash
# Backend logs
railway logs --service backend

# Sensor Simulator logs
railway logs --service sensor-simulator

# Frontend logs
railway logs --service frontend
```

### Check Service Status

```bash
railway status
```

### Restart a Service

```bash
railway restart --service <service-name>
```

### View Environment Variables

```bash
railway variables --service <service-name>
```

---

## Common Issues & Solutions

### Issue 1: CORS Errors in Browser

**Symptom**: Frontend shows CORS errors in console

**Solution**:
1. Ensure frontend URL is in backend CORS_ORIGINS
2. Redeploy backend after updating CORS
3. Clear browser cache

### Issue 2: WebSocket Connection Failed

**Symptom**: Real-time updates not working

**Solution**:
1. Check if backend WebSocket endpoint is accessible
2. Verify WebSocket URL in frontend (wss:// for HTTPS)
3. Check Railway logs for WebSocket errors

### Issue 3: 502 Bad Gateway

**Symptom**: Service returns 502 error

**Solution**:
1. Check service logs: `railway logs --service <service-name>`
2. Verify health check endpoint is responding
3. Check if service is running: `railway status`
4. Restart service if needed: `railway restart --service <service-name>`

### Issue 4: Database Connection Failed

**Symptom**: Backend can't connect to database

**Solution**:
1. Verify DATABASE_URL environment variable
2. Check PostgreSQL service status
3. Ensure database migrations have run
4. Check connection pool settings (NullPool for Railway)

---

## Post-Deployment Checklist

- [ ] Backend health endpoint responds (200 OK)
- [ ] Sensor simulator health endpoint responds (200 OK)
- [ ] Frontend loads in browser
- [ ] Login works with admin credentials
- [ ] Dashboard shows data
- [ ] Navigation between pages works
- [ ] Alerts page loads with statistics
- [ ] Simulator control panel can start simulation
- [ ] WebSocket real-time updates work
- [ ] Scenario application works
- [ ] Alert acknowledgment works
- [ ] CORS is configured correctly

---

## URLs Reference

After deployment, save these URLs:

```
Backend API: https://backend-production-6266.up.railway.app
Sensor Simulator: https://sensor-simulator-production.up.railway.app
Frontend: https://frontend-production.up.railway.app

API Docs: https://backend-production-6266.up.railway.app/docs
Simulator Docs: https://sensor-simulator-production.up.railway.app/docs
```

---

## Next Steps After Deployment

1. **Generate Training Data**
   - Use Kaggle GPU for faster generation
   - Repository: https://github.com/khiwniti/battery-rul-data-generation
   - Follow: KAGGLE_SETUP.md

2. **Load Training Data**
   - Upload generated CSV files to Railway PostgreSQL
   - Run data loading scripts

3. **Train ML Models**
   - Use Battery_RUL_Training.ipynb
   - Deploy trained models to ML Pipeline service

4. **Enable Real-Time Predictions**
   - Start sensor simulator
   - Backend generates RUL predictions
   - Frontend displays predictions

5. **Production Monitoring**
   - Set up Railway monitoring alerts
   - Configure log retention
   - Set up backup schedules

---

## Support & Documentation

- **Project Documentation**: See SYSTEM_COMPLETE_SUMMARY.md
- **Sensor Simulator Guide**: See sensor-simulator/README.md
- **Backend API**: See DEPLOYMENT_SUCCESS.md
- **Data Generation**: See KAGGLE_SETUP.md
- **Railway Docs**: https://docs.railway.app

---

**Last Updated**: December 1, 2025
**System Version**: v1.0.0-beta
**Status**: Ready for Production Deployment
