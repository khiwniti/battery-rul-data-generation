# Battery Sensor Simulator

Real-time battery telemetry simulator with scenario-based testing capabilities for the Battery RUL Prediction system.

## Features

- **Real-time Telemetry Generation**: Generates realistic battery sensor data with physics-based degradation
- **WebSocket Streaming**: Real-time data streaming to connected clients
- **Scenario-Based Testing**: Apply various operational scenarios (power outages, HVAC failures, thermal events)
- **Multiple Degradation Profiles**: Simulate healthy, accelerated aging, and failing batteries
- **RESTful API**: Complete control via HTTP endpoints

## Quick Start

### Local Development

```bash
# Install dependencies (FastAPI, numpy, pandas already available in environment)
cd sensor-simulator

# Start the service
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8003 --reload
```

### Test the API

```bash
# Run the test script
python test_api.py
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Start Simulation
```bash
POST /api/v1/simulation/start
Content-Type: application/json

{
  "batteries": [
    {
      "battery_id": "BKK_DC1_SYS01_STR01_BAT001",
      "profile": "healthy",  // healthy | accelerated | failing
      "initial_soh": 95.0
    }
  ],
  "interval_seconds": 5,
  "scenario": "normal_operation"  // optional
}
```

### Stop Simulation
```bash
POST /api/v1/simulation/stop
```

### Get Status
```bash
GET /api/v1/simulation/status
```

### List Scenarios
```bash
GET /api/v1/scenarios
```

Returns available test scenarios:
- **normal_operation**: Standard float charging at 25°C
- **high_temperature**: Elevated ambient (45°C) - simulates hot season
- **power_outage**: Battery discharge under load
- **hvac_failure**: AC failure causing temperature rise
- **battery_degradation**: Accelerated aging with high resistance
- **thermal_runaway**: Critical temperature event (65-75°C)

### Apply Scenario
```bash
POST /api/v1/scenarios/apply
Content-Type: application/json

{
  "scenario": "power_outage",
  "battery_ids": ["BKK_DC1_SYS01_STR01_BAT001"],  // optional, null = all
  "ambient_temp": 28.0  // optional override
}
```

### Clear Scenario
```bash
POST /api/v1/scenarios/clear
Content-Type: application/json

{
  "battery_ids": ["BKK_DC1_SYS01_STR01_BAT001"]  // optional, null = all
}
```

### WebSocket Real-time Stream
```javascript
const ws = new WebSocket('ws://localhost:8003/api/v1/ws/telemetry');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'telemetry') {
    // message.data contains array of telemetry readings
    console.log('Telemetry:', message.data);
  } else if (message.type === 'ping') {
    // Keep-alive ping
  }
};
```

## Telemetry Data Format

Each telemetry reading includes:

```json
{
  "battery_id": "BKK_DC1_SYS01_STR01_BAT001",
  "timestamp": "2025-12-01T03:09:15.234Z",
  "voltage_v": 13.652,
  "current_a": 0.523,
  "temperature_c": 26.45,
  "internal_resistance_mohm": 3.542,
  "soh_pct": 94.87,
  "mode": "float"  // float | discharge | boost | equalize
}
```

## Degradation Profiles

### Healthy (85% of fleet)
- 1% SOH decline per year
- 5% resistance increase per year
- Minimal failure probability

### Accelerated (12% of fleet)
- 8% SOH decline per year
- 15% resistance increase per year
- Moderate failure risk

### Failing (3% of fleet)
- 25% SOH decline per year
- 40% resistance increase per year
- High failure probability
- Simulates end-of-life batteries

## Physics-Based Modeling

The simulator implements:

- **Arrhenius Temperature Acceleration**: Every +10°C doubles aging rate
- **Cycling Stress**: Depth-of-discharge dependent (DOD²)
- **Calendar Aging**: Time-based capacity fade
- **Float Voltage Stress**: Overcharging accelerates grid corrosion
- **Mode-Specific Behavior**: Different voltage/current/temperature for each operating mode

## Deployment

### Railway.com

The service includes `railway.json` for easy deployment:

```bash
# Deploy to Railway
railway up

# Set environment variables
railway variables --set PORT=8003

# Check logs
railway logs
```

## Integration with Main System

The sensor simulator is designed to work with:

1. **Backend API** (port 8000): Main application backend
2. **Frontend** (port 3000): React dashboard with control panel
3. **ML Pipeline** (port 8001): Training and prediction service

### Architecture Flow

```
Frontend Control Panel
    ↓ (REST API)
Sensor Simulator ← scenario controls
    ↓ (WebSocket)
Frontend Dashboard (real-time telemetry display)
    ↓ (HTTP POST)
Backend API (stores telemetry in database)
    ↓
ML Pipeline (uses data for training/prediction)
```

## Use Cases

1. **Development Testing**: Generate test data without physical batteries
2. **Scenario Testing**: Validate alert rules and prediction models
3. **Demo**: Show system behavior under various conditions
4. **Training Data**: Generate synthetic data for ML model training
5. **Load Testing**: Test system performance under high telemetry volume

## Configuration

Edit `src/telemetry_generator.py` to customize:
- Base voltage (default: 12.0V per battery jar)
- Temperature ranges
- Degradation rates
- Noise levels

## Monitoring

Check simulation status:
```bash
curl http://localhost:8003/api/v1/simulation/status
```

Watch logs:
```bash
# Local
tail -f logs/sensor-simulator.log

# Railway
railway logs --service sensor-simulator
```

## Next Steps

- [ ] Deploy to Railway
- [ ] Create control panel UI component in frontend
- [ ] Add scenario scheduling (e.g., daily power outage at 14:00)
- [ ] Implement battery fleet presets (9 locations × 24 batteries)
- [ ] Add telemetry recording to CSV for offline analysis
