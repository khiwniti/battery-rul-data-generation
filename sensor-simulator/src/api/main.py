"""
Sensor Simulator Service
Generates realistic battery telemetry data with control panel
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Optional

from ..schemas import (
    SimulationStartRequest,
    SimulationStatus,
    ScenarioRequest,
    ScenarioInfo,
    ScenarioType,
)
from ..simulation_manager import simulation_manager


app = FastAPI(
    title="Sensor Simulator Service",
    version="1.0.0",
    description="Battery sensor data simulator with scenario control panel",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway.com"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "sensor-simulator",
            "version": "1.0.0",
        },
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sensor Simulator Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "start_simulation": "POST /api/v1/simulation/start",
            "stop_simulation": "POST /api/v1/simulation/stop",
            "get_status": "GET /api/v1/simulation/status",
            "scenarios": "GET /api/v1/scenarios",
            "apply_scenario": "POST /api/v1/scenarios/apply",
            "clear_scenario": "POST /api/v1/scenarios/clear",
            "websocket": "WS /api/v1/ws/telemetry",
        },
    }


@app.post("/api/v1/simulation/start", response_model=dict)
async def start_simulation(request: SimulationStartRequest):
    """
    Start sensor data simulation for specified batteries

    Generates realistic telemetry based on scenario parameters
    """
    try:
        await simulation_manager.start_simulation(
            batteries=request.batteries,
            interval_seconds=request.interval_seconds,
            scenario=request.scenario,
        )
        return {
            "status": "started",
            "message": f"Simulation started for {len(request.batteries)} batteries",
            "interval_seconds": request.interval_seconds,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/simulation/stop", response_model=dict)
async def stop_simulation():
    """
    Stop all active simulations
    """
    await simulation_manager.stop_simulation()
    return {
        "status": "stopped",
        "message": "Simulation stopped successfully",
    }


@app.get("/api/v1/simulation/status", response_model=SimulationStatus)
async def get_simulation_status():
    """
    Get current simulation status
    """
    return simulation_manager.get_status()


@app.get("/api/v1/scenarios", response_model=List[ScenarioInfo])
async def list_scenarios():
    """
    List available test scenarios

    Examples: normal_operation, high_temperature, power_outage,
             hvac_failure, battery_degradation, thermal_runaway
    """
    scenarios = [
        ScenarioInfo(
            scenario=ScenarioType.NORMAL_OPERATION,
            name="Normal Operation",
            description="Standard float charging at 25°C ambient temperature",
            typical_conditions={
                "voltage": "13.65V",
                "temperature": "25-27°C",
                "mode": "float",
            },
        ),
        ScenarioInfo(
            scenario=ScenarioType.HIGH_TEMPERATURE,
            name="High Temperature",
            description="Elevated ambient temperature (45°C) - simulates hot season or HVAC degradation",
            typical_conditions={
                "voltage": "13.65V",
                "temperature": "45-48°C",
                "mode": "float",
            },
        ),
        ScenarioInfo(
            scenario=ScenarioType.POWER_OUTAGE,
            name="Power Outage",
            description="Battery discharging under load during utility power failure",
            typical_conditions={
                "voltage": "11.5-12.0V",
                "temperature": "30-35°C",
                "mode": "discharge",
                "current": "-10 to -30A",
            },
        ),
        ScenarioInfo(
            scenario=ScenarioType.HVAC_FAILURE,
            name="HVAC Failure",
            description="Air conditioning system failure causing temperature rise",
            typical_conditions={
                "voltage": "13.65V",
                "temperature": "40-50°C",
                "mode": "float",
            },
        ),
        ScenarioInfo(
            scenario=ScenarioType.BATTERY_DEGRADATION,
            name="Battery Degradation",
            description="Accelerated aging with increased internal resistance and capacity fade",
            typical_conditions={
                "voltage": "13.5-13.7V (lower under load)",
                "temperature": "28-35°C (runs hotter)",
                "resistance": "Increasing",
                "soh": "Declining rapidly",
            },
        ),
        ScenarioInfo(
            scenario=ScenarioType.THERMAL_RUNAWAY,
            name="Thermal Runaway",
            description="Critical temperature event - battery overheating due to internal short or failure",
            typical_conditions={
                "voltage": "Variable",
                "temperature": "65-75°C (critical)",
                "mode": "discharge",
            },
        ),
    ]
    return scenarios


@app.post("/api/v1/scenarios/apply", response_model=dict)
async def apply_scenario(request: ScenarioRequest):
    """
    Apply a predefined scenario to simulation

    Allows testing various operational conditions
    """
    if not simulation_manager.is_running:
        raise HTTPException(status_code=400, detail="No active simulation")

    simulation_manager.apply_scenario(
        scenario=request.scenario,
        battery_ids=request.battery_ids,
        ambient_temp=request.ambient_temp,
    )

    target = (
        f"{len(request.battery_ids)} batteries"
        if request.battery_ids
        else "all batteries"
    )

    return {
        "status": "applied",
        "message": f"Scenario '{request.scenario.value}' applied to {target}",
    }


@app.post("/api/v1/scenarios/clear", response_model=dict)
async def clear_scenario(battery_ids: Optional[List[str]] = None):
    """
    Clear scenario overrides
    """
    simulation_manager.clear_scenario(battery_ids)

    target = (
        f"{len(battery_ids)} batteries"
        if battery_ids
        else "all batteries"
    )

    return {
        "status": "cleared",
        "message": f"Scenarios cleared for {target}",
    }


@app.websocket("/api/v1/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry streaming

    Clients connect to receive live telemetry data as it's generated
    """
    await websocket.accept()

    # Subscribe to telemetry updates
    queue = await simulation_manager.subscribe()

    try:
        while True:
            # Get telemetry from queue
            try:
                readings = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json({
                    "type": "telemetry",
                    "data": readings,
                })
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Unsubscribe when client disconnects
        await simulation_manager.unsubscribe(queue)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )
