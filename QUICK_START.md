# Battery RUL System - Quick Start Guide

## 🚀 Deployment in 3 Steps

### Step 1: Deploy Sensor Simulator
```bash
cd /teamspace/studios/this_studio/NT/RUL_prediction
./deploy-sensor-simulator.sh
```

### Step 2: Deploy Frontend
```bash
./deploy-frontend.sh
```

### Step 3: Access the System
```
Backend: https://backend-production-6266.up.railway.app
Login: admin / Admin123!
```

---

## 📚 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| `DEPLOYMENT_GUIDE.md` | Complete deployment instructions |
| `SYSTEM_COMPLETE_SUMMARY.md` | Full system overview |
| `SESSION_FINAL.md` | What was built this session |
| `sensor-simulator/README.md` | Simulator usage guide |

---

## 🎯 What's Been Built

### ✅ Completed
- Backend API (28 endpoints) - DEPLOYED
- PostgreSQL Database - DEPLOYED  
- Sensor Simulator (8 endpoints) - TESTED
- Frontend (6 pages) - COMPLETE
- Deployment automation - READY
- Documentation - COMPLETE

### 📝 Next Steps
1. Deploy sensor simulator
2. Deploy frontend
3. Integration testing
4. Generate training data
5. Train ML models

---

## 🔑 Key URLs

- Backend API: https://backend-production-6266.up.railway.app
- API Docs: https://backend-production-6266.up.railway.app/docs
- Data Repo: https://github.com/khiwniti/battery-rul-data-generation

---

## 💡 Quick Tips

### Test Backend
```bash
curl https://backend-production-6266.up.railway.app/health
```

### Check Railway Status
```bash
railway status
```

### View Logs
```bash
railway logs --service backend
railway logs --service sensor-simulator
railway logs --service frontend
```

---

**Status**: 85% Complete - Ready for Deployment
**Next Action**: Run deployment scripts
