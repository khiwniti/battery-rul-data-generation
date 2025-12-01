"""
Simulation Manager
Manages active simulations and coordinates telemetry generation
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

from .telemetry_generator import TelemetryGenerator, BatteryProfile
from .schemas import (
    BatteryConfig,
    ScenarioType,
    SimulationStatus,
    TelemetryReading,
    OperatingMode,
)


class SimulationManager:
    """Manages battery telemetry simulation"""

    def __init__(self):
        self.generator = TelemetryGenerator()
        self.is_running = False
        self.interval_seconds = 5
        self.started_at: Optional[datetime] = None
        self.readings_generated = 0
        self.active_batteries: Set[str] = set()
        self.current_scenario: Optional[ScenarioType] = None
        self.scenario_overrides: Dict[str, dict] = {}  # Per-battery scenario settings
        self._task: Optional[asyncio.Task] = None
        self._subscribers: Set[asyncio.Queue] = set()

    async def start_simulation(
        self,
        batteries: List[BatteryConfig],
        interval_seconds: int = 5,
        scenario: Optional[ScenarioType] = None,
    ):
        """Start telemetry simulation"""
        if self.is_running:
            raise RuntimeError("Simulation already running")

        # Initialize batteries
        for battery in batteries:
            profile = BatteryProfile(battery.profile.value)
            self.generator.initialize_battery(
                battery.battery_id,
                profile=profile,
                initial_soh=battery.initial_soh,
            )
            self.active_batteries.add(battery.battery_id)

        self.interval_seconds = interval_seconds
        self.current_scenario = scenario
        self.started_at = datetime.utcnow()
        self.readings_generated = 0
        self.is_running = True

        # Start background task
        self._task = asyncio.create_task(self._generation_loop())

    async def stop_simulation(self):
        """Stop active simulation"""
        if not self.is_running:
            return

        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.active_batteries.clear()
        self.current_scenario = None
        self.scenario_overrides.clear()

    def get_status(self) -> SimulationStatus:
        """Get current simulation status"""
        return SimulationStatus(
            is_running=self.is_running,
            batteries_count=len(self.active_batteries),
            interval_seconds=self.interval_seconds,
            scenario=self.current_scenario,
            started_at=self.started_at,
            readings_generated=self.readings_generated,
        )

    def apply_scenario(
        self,
        scenario: ScenarioType,
        battery_ids: Optional[List[str]] = None,
        ambient_temp: Optional[float] = None,
    ):
        """Apply scenario to specific batteries or all"""
        target_batteries = battery_ids if battery_ids else list(self.active_batteries)

        for battery_id in target_batteries:
            if battery_id in self.active_batteries:
                self.scenario_overrides[battery_id] = {
                    "scenario": scenario,
                    "ambient_temp": ambient_temp,
                }

    def clear_scenario(self, battery_ids: Optional[List[str]] = None):
        """Clear scenario overrides"""
        if battery_ids:
            for battery_id in battery_ids:
                self.scenario_overrides.pop(battery_id, None)
        else:
            self.scenario_overrides.clear()
            self.current_scenario = None

    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to telemetry updates"""
        queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from telemetry updates"""
        self._subscribers.discard(queue)

    async def _generation_loop(self):
        """Background task that generates telemetry at regular intervals"""
        try:
            while self.is_running:
                # Generate telemetry for all active batteries
                readings = []
                for battery_id in self.active_batteries:
                    reading = self._generate_reading(battery_id)
                    readings.append(reading)

                self.readings_generated += len(readings)

                # Broadcast to all subscribers
                await self._broadcast(readings)

                # Wait for next interval
                await asyncio.sleep(self.interval_seconds)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in generation loop: {e}")
            self.is_running = False

    def _generate_reading(self, battery_id: str) -> TelemetryReading:
        """Generate single telemetry reading for a battery"""
        # Check for battery-specific scenario
        if battery_id in self.scenario_overrides:
            override = self.scenario_overrides[battery_id]
            telemetry = self.generator.simulate_scenario(
                battery_id,
                scenario=override["scenario"].value,
                ambient_temp=override.get("ambient_temp"),
            )
        elif self.current_scenario:
            # Apply global scenario
            telemetry = self.generator.simulate_scenario(
                battery_id,
                scenario=self.current_scenario.value,
            )
        else:
            # Normal operation
            telemetry = self.generator.generate_telemetry(battery_id)

        # Convert to TelemetryReading
        return TelemetryReading(
            battery_id=telemetry["battery_id"],
            timestamp=datetime.fromisoformat(telemetry["timestamp"]),
            voltage_v=telemetry["voltage_v"],
            current_a=telemetry["current_a"],
            temperature_c=telemetry["temperature_c"],
            internal_resistance_mohm=telemetry["internal_resistance_mohm"],
            soh_pct=telemetry["soh_pct"],
            mode=OperatingMode(telemetry["mode"]),
        )

    async def _broadcast(self, readings: List[TelemetryReading]):
        """Broadcast readings to all subscribers"""
        if not self._subscribers:
            return

        # Convert readings to dict
        data = [reading.model_dump(mode="json") for reading in readings]

        # Send to all subscribers (non-blocking)
        dead_subscribers = set()
        for queue in self._subscribers:
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                # Skip if queue is full
                pass
            except Exception:
                dead_subscribers.add(queue)

        # Clean up dead subscribers
        self._subscribers -= dead_subscribers


# Global simulation manager instance
simulation_manager = SimulationManager()
