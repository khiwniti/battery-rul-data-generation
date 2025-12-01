"""
Battery Telemetry Generator
Generates realistic battery sensor data with degradation simulation
"""
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum


class BatteryProfile(Enum):
    """Battery degradation profiles"""
    HEALTHY = "healthy"
    ACCELERATED = "accelerated"
    FAILING = "failing"


class BatteryState:
    """Tracks battery state for realistic degradation simulation"""

    def __init__(
        self,
        battery_id: str,
        profile: BatteryProfile = BatteryProfile.HEALTHY,
        initial_soh: float = 100.0,
        base_voltage: float = 12.0,
        base_temp: float = 25.0,
    ):
        self.battery_id = battery_id
        self.profile = profile
        self.soh_pct = initial_soh
        self.base_voltage = base_voltage
        self.base_temp = base_temp
        self.internal_resistance_mohm = 3.5  # Initial resistance
        self.charge_cycles = 0
        self.last_update = datetime.utcnow()

        # Degradation rates based on profile
        if profile == BatteryProfile.HEALTHY:
            self.degradation_rate = 0.01 / 365  # 1% per year
            self.resistance_increase = 0.05 / 365  # 5% per year
        elif profile == BatteryProfile.ACCELERATED:
            self.degradation_rate = 0.08 / 365  # 8% per year
            self.resistance_increase = 0.15 / 365  # 15% per year
        else:  # FAILING
            self.degradation_rate = 0.25 / 365  # 25% per year
            self.resistance_increase = 0.40 / 365  # 40% per year

    def update_degradation(self, time_delta_seconds: float):
        """Update battery degradation based on time elapsed"""
        days_elapsed = time_delta_seconds / 86400

        # Calendar aging
        self.soh_pct -= self.degradation_rate * days_elapsed
        self.internal_resistance_mohm += self.resistance_increase * days_elapsed

        # Ensure SOH doesn't go below 0
        self.soh_pct = max(0, self.soh_pct)


class TelemetryGenerator:
    """Generates realistic battery telemetry data"""

    def __init__(self):
        self.battery_states: Dict[str, BatteryState] = {}

    def initialize_battery(
        self,
        battery_id: str,
        profile: BatteryProfile = BatteryProfile.HEALTHY,
        initial_soh: float = 100.0,
    ):
        """Initialize or reset a battery's state"""
        self.battery_states[battery_id] = BatteryState(
            battery_id=battery_id,
            profile=profile,
            initial_soh=initial_soh,
        )

    def generate_telemetry(
        self,
        battery_id: str,
        mode: str = "float",
        ambient_temp: float = 25.0,
    ) -> Dict:
        """
        Generate realistic telemetry reading for a battery

        Args:
            battery_id: Battery identifier
            mode: Operating mode (float, discharge, boost, equalize)
            ambient_temp: Ambient temperature in Celsius

        Returns:
            Dictionary with telemetry data
        """
        # Get or create battery state
        if battery_id not in self.battery_states:
            self.initialize_battery(battery_id)

        state = self.battery_states[battery_id]

        # Update degradation
        now = datetime.utcnow()
        time_delta = (now - state.last_update).total_seconds()
        state.update_degradation(time_delta)
        state.last_update = now

        # Generate voltage based on mode and SOH
        voltage = self._generate_voltage(state, mode)

        # Generate temperature (affected by load and ambient)
        temperature = self._generate_temperature(state, mode, ambient_temp)

        # Generate current based on mode
        current = self._generate_current(mode)

        # Add realistic noise
        voltage += random.gauss(0, 0.02)
        temperature += random.gauss(0, 0.3)
        current += random.gauss(0, 0.1)

        return {
            "battery_id": battery_id,
            "timestamp": now.isoformat(),
            "voltage_v": round(voltage, 3),
            "current_a": round(current, 3),
            "temperature_c": round(temperature, 2),
            "internal_resistance_mohm": round(state.internal_resistance_mohm, 3),
            "soh_pct": round(state.soh_pct, 2),
            "mode": mode,
        }

    def _generate_voltage(self, state: BatteryState, mode: str) -> float:
        """Generate voltage based on mode and SOH"""
        base_voltages = {
            "float": 13.65,  # Float charging
            "discharge": 11.5 + (state.soh_pct / 100) * 0.5,  # Under load
            "boost": 14.0,  # Boost charging
            "equalize": 14.4,  # Equalization
        }

        voltage = base_voltages.get(mode, 13.65)

        # SOH affects voltage under load
        if mode == "discharge":
            voltage *= (0.95 + (state.soh_pct / 100) * 0.05)

        return voltage

    def _generate_temperature(
        self,
        state: BatteryState,
        mode: str,
        ambient_temp: float
    ) -> float:
        """Generate temperature based on mode and ambient"""
        # Base temperature close to ambient
        temperature = ambient_temp

        # Add heat from charging/discharging
        if mode == "discharge":
            temperature += 5 + (state.internal_resistance_mohm / 5.0) * 3
        elif mode in ["boost", "equalize"]:
            temperature += 3 + (state.internal_resistance_mohm / 5.0) * 2
        else:  # float
            temperature += 1

        # Degraded batteries run hotter
        if state.soh_pct < 80:
            temperature += (100 - state.soh_pct) / 10

        return temperature

    def _generate_current(self, mode: str) -> float:
        """Generate current based on operating mode"""
        currents = {
            "float": 0.5 + random.random() * 0.3,  # Trickle charge
            "discharge": -(10 + random.random() * 20),  # Discharge (negative)
            "boost": 5 + random.random() * 3,  # Fast charge
            "equalize": 2 + random.random() * 1,  # Slow overcharge
        }
        return currents.get(mode, 0.5)

    def simulate_scenario(
        self,
        battery_id: str,
        scenario: str,
        ambient_temp: Optional[float] = None,
    ) -> Dict:
        """
        Simulate specific test scenarios

        Scenarios:
        - normal_operation: Standard float charging
        - high_temperature: Elevated ambient temp (simulates HVAC failure)
        - power_outage: Battery discharge under load
        - battery_degradation: Accelerated aging
        - thermal_runaway: Critical temperature event
        """
        if scenario == "normal_operation":
            return self.generate_telemetry(battery_id, mode="float", ambient_temp=25.0)

        elif scenario == "high_temperature":
            return self.generate_telemetry(battery_id, mode="float", ambient_temp=45.0)

        elif scenario == "power_outage":
            return self.generate_telemetry(battery_id, mode="discharge", ambient_temp=ambient_temp or 25.0)

        elif scenario == "battery_degradation":
            # Temporarily set to failing profile
            if battery_id not in self.battery_states:
                self.initialize_battery(battery_id, profile=BatteryProfile.FAILING)
            else:
                self.battery_states[battery_id].profile = BatteryProfile.FAILING
            return self.generate_telemetry(battery_id, mode="float", ambient_temp=ambient_temp or 25.0)

        elif scenario == "thermal_runaway":
            telemetry = self.generate_telemetry(battery_id, mode="discharge", ambient_temp=50.0)
            telemetry["temperature_c"] = 65.0 + random.random() * 10  # Critical temp
            return telemetry

        else:
            return self.generate_telemetry(battery_id, mode="float", ambient_temp=ambient_temp or 25.0)
