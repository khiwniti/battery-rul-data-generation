"""
Telemetry Data Generator

Generates realistic time-series telemetry data:
- Per-battery telemetry (voltage, temperature, resistance)
- Per-string telemetry (voltage, current, mode, ripple)
- Environmental telemetry (temperature, humidity, HVAC status)

Includes realistic operational scenarios:
- Float charging (normal operation)
- Discharge events (power outages)
- Equalization charging (maintenance)
- Load variations
- Temperature effects
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from battery_degradation import BatteryDegradationModel
from thailand_environment import ThailandEnvironmentModel


class TelemetryGenerator:
    """Generate realistic battery telemetry data."""

    # Operating modes
    MODES = ['float', 'boost', 'discharge', 'idle', 'equalize']

    # Float voltage target (center of range)
    FLOAT_VOLTAGE_TARGET = 13.65  # V per jar

    # Discharge current ranges by system type
    DISCHARGE_CURRENT_RANGE = {
        'RECTIFIER': (50, 150),  # DC loads
        'UPS': (80, 200)  # AC loads through UPS
    }

    # Thermal model parameters (RC thermal network)
    # Based on typical VRLA battery thermal characteristics
    THERMAL_RESISTANCE_C_PER_W = 1.5  # Kelvin/Watt (battery to ambient)
    THERMAL_CAPACITANCE_J_PER_C = 5000.0  # Joules/Kelvin (heat capacity ~5 kg battery)
    THERMAL_TIME_CONSTANT_S = THERMAL_RESISTANCE_C_PER_W * THERMAL_CAPACITANCE_J_PER_C  # ~7500s = 2.1 hours

    def __init__(
        self,
        battery_models: Dict[str, BatteryDegradationModel],
        string_info: pd.DataFrame,
        location_region: str,
        system_type: str,
        seed: int = None
    ):
        """
        Initialize telemetry generator.

        Args:
            battery_models: Dictionary of battery degradation models {battery_id: model}
            string_info: String configuration DataFrame
            location_region: Thai region for environmental model
            system_type: 'UPS' or 'RECTIFIER'
            seed: Random seed
        """
        self.battery_models = battery_models
        self.string_info = string_info
        self.location_region = location_region
        self.system_type = system_type

        # Initialize environmental model
        self.env_model = ThailandEnvironmentModel(location_region, seed=seed)

        # State variables
        self.current_mode = 'float'
        self.current_soc = {bid: 100.0 for bid in battery_models.keys()}
        self.current_temp = {bid: 25.0 for bid in battery_models.keys()}  # Track battery temperature (°C)
        self.grid_available = True
        self.discharge_event_active = False

        if seed is not None:
            np.random.seed(seed)

    def determine_mode(
        self,
        timestamp: datetime,
        grid_available: bool,
        scheduled_equalize: bool = False
    ) -> str:
        """
        Determine operating mode based on conditions.

        Args:
            timestamp: Current time
            grid_available: Is grid power available
            scheduled_equalize: Is equalization scheduled

        Returns:
            Operating mode
        """
        if not grid_available:
            return 'discharge'
        elif scheduled_equalize:
            return 'equalize'
        elif self.current_mode == 'discharge':
            # After discharge, boost charge to recover
            if min(self.current_soc.values()) < 95:
                return 'boost'
            else:
                return 'float'
        elif self.current_mode == 'boost':
            # Return to float when fully charged
            if min(self.current_soc.values()) >= 99:
                return 'float'
            else:
                return 'boost'
        else:
            return 'float'

    def generate_string_current(
        self,
        mode: str,
        timestamp: datetime,
        load_factor: float = 0.8
    ) -> float:
        """
        Generate realistic string current based on mode and load.

        Args:
            mode: Operating mode
            timestamp: Current time
            load_factor: Load factor (0-1)

        Returns:
            Current in amperes (positive = charge, negative = discharge)
        """
        if mode == 'float':
            # Float current is very low (just compensating self-discharge)
            current = np.random.uniform(0.5, 2.0)

        elif mode == 'boost':
            # Boost charging current (recovering from discharge)
            # Current decreases as SOC increases
            avg_soc = np.mean(list(self.current_soc.values()))
            max_current = 30.0  # Max charge current

            if avg_soc < 80:
                current = max_current * np.random.uniform(0.8, 1.0)
            elif avg_soc < 90:
                current = max_current * np.random.uniform(0.5, 0.7)
            else:
                current = max_current * np.random.uniform(0.2, 0.4)

        elif mode == 'discharge':
            # Discharge current based on load and system type
            current_range = self.DISCHARGE_CURRENT_RANGE[self.system_type]
            base_current = np.random.uniform(*current_range)

            # Apply load factor
            current = -base_current * load_factor  # Negative for discharge

        elif mode == 'equalize':
            # Equalization is like boost but slightly higher voltage
            current = np.random.uniform(5.0, 15.0)

        else:  # idle
            current = 0.0

        # Add realistic noise
        current += np.random.normal(0, abs(current) * 0.02)

        return round(current, 3)

    def update_soc(
        self,
        current_a: float,
        delta_time_hours: float
    ):
        """
        Update state of charge for all batteries using coulomb counting.

        Args:
            current_a: String current (positive = charge, negative = discharge)
            delta_time_hours: Time step
        """
        # Coulomb counting: ΔQ = I * Δt
        ah_change = current_a * delta_time_hours

        for battery_id, model in self.battery_models.items():
            current_capacity = model.current_capacity_ah

            # Update SOC (protect against zero capacity)
            if current_capacity > 0:
                soc_change = (ah_change / current_capacity) * 100.0
                new_soc = np.clip(self.current_soc[battery_id] + soc_change, 0, 100)
                self.current_soc[battery_id] = new_soc
            else:
                new_soc = 0
                self.current_soc[battery_id] = 0

            # If discharging, accumulate cycle stress
            if current_a < 0:
                ah_throughput = abs(ah_change)
                dod_pct = 100 - new_soc
                # Temperature will be updated in main loop
                model.cumulative_ah_throughput += ah_throughput

    def generate_jar_telemetry(
        self,
        timestamp: datetime,
        battery_id: str,
        string_current_a: float,
        ambient_temp_c: float,
        mode: str
    ) -> Dict:
        """
        Generate per-battery (jar) telemetry.

        Args:
            timestamp: Current time
            battery_id: Battery identifier
            string_current_a: String current
            ambient_temp_c: Ambient temperature
            mode: Operating mode

        Returns:
            Dictionary of telemetry values
        """
        model = self.battery_models[battery_id]
        soc = self.current_soc[battery_id]

        # PRODUCTION-GRADE THERMAL MODEL
        # Use RC thermal network: C_th * dT/dt = P_heat - (T - T_ambient) / R_th
        # This provides realistic thermal dynamics with proper time constants

        # Get previous battery temperature
        prev_battery_temp = self.current_temp.get(battery_id, ambient_temp_c)

        # Calculate heat generation from Joule heating (I²R losses)
        # Power dissipated = I² * R_internal
        resistance_ohm = model.current_resistance_mohm * 0.001
        power_dissipated_w = (string_current_a ** 2) * resistance_ohm

        # Steady-state temperature rise at current power level
        # ΔT_ss = P * R_thermal
        temp_rise_steady_state = power_dissipated_w * self.THERMAL_RESISTANCE_C_PER_W

        # Realistic limit on steady-state rise (max 15°C for VRLA in normal operation)
        temp_rise_steady_state = np.clip(temp_rise_steady_state, 0, 15.0)

        # Target temperature (what battery will eventually reach)
        target_temp = ambient_temp_c + temp_rise_steady_state

        # First-order thermal dynamics: T(t) approaches target with exponential time constant
        # Assuming time step of ~60 seconds (typical sampling interval)
        dt_seconds = 60.0
        alpha = 1 - np.exp(-dt_seconds / self.THERMAL_TIME_CONSTANT_S)  # Thermal time constant ~7500s

        # Update temperature: exponential approach to target
        battery_temp = prev_battery_temp + alpha * (target_temp - prev_battery_temp)

        # Add measurement noise (±0.5°C typical for thermistor)
        battery_temp += np.random.normal(0, 0.5)

        # Safety limits: VRLA batteries operate 10-50°C range
        battery_temp = np.clip(battery_temp, 10.0, 50.0)

        # Store updated temperature for next iteration
        self.current_temp[battery_id] = battery_temp

        # Terminal voltage
        voltage = model.get_terminal_voltage(
            soc,
            string_current_a,
            battery_temp
        )

        # Resistance (from model, with measurement noise)
        resistance = model.current_resistance_mohm
        resistance += np.random.normal(0, resistance * 0.02)

        # Conductance (inverse of resistance)
        conductance = 1.0 / (resistance * 0.001) if resistance > 0 else 0

        return {
            'ts': timestamp,
            'battery_id': battery_id,
            'voltage_v': round(voltage, 3),
            'temperature_c': round(battery_temp, 1),
            'resistance_mohm': round(resistance, 3),
            'conductance_s': round(conductance, 5),
            'soc_pct': round(soc, 2),  # Include accurate SOC from coulomb counting
            'soh_pct': round(model.current_soh_pct, 2)  # Include SOH from degradation model
        }

    def generate_string_telemetry(
        self,
        timestamp: datetime,
        string_id: str,
        string_current_a: float,
        mode: str,
        battery_voltages: List[float]
    ) -> Dict:
        """
        Generate per-string telemetry.

        Args:
            timestamp: Current time
            string_id: String identifier
            string_current_a: String current
            mode: Operating mode
            battery_voltages: List of individual battery voltages

        Returns:
            Dictionary of telemetry values
        """
        # String voltage is sum of battery voltages
        string_voltage = sum(battery_voltages)

        # Add string-level voltage measurement noise
        string_voltage += np.random.normal(0, 0.2)

        # Ripple voltage (AC component on DC bus)
        # Higher during float/boost (from rectifier)
        if mode in ['float', 'boost', 'equalize']:
            ripple_base = 0.5  # 500 mV RMS base
            # Worse ripple if rectifier aging or high load
            ripple_factor = np.random.uniform(0.8, 1.5)
            ripple_voltage_rms = ripple_base * ripple_factor
        else:
            # Very low ripple during discharge (battery output is clean DC)
            ripple_voltage_rms = np.random.uniform(0.05, 0.15)

        # Ripple current
        # Assuming ~1% ripple current (typical for good power systems)
        ripple_current_rms = abs(string_current_a) * 0.01 * np.random.uniform(0.5, 2.0)

        # Flags
        equalize_flag = (mode == 'equalize')
        generator_test_flag = False  # Could add scheduled generator tests

        # Transfer switch event (mode change to discharge)
        transfer_event_flag = (
            mode == 'discharge' and
            self.current_mode != 'discharge'
        )

        return {
            'ts': timestamp,
            'string_id': string_id,
            'voltage_v': round(string_voltage, 2),
            'current_a': round(string_current_a, 3),
            'mode': mode,
            'ripple_voltage_rms_v': round(ripple_voltage_rms, 3),
            'ripple_current_rms_a': round(ripple_current_rms, 3),
            'equalize_flag': equalize_flag,
            'generator_test_flag': generator_test_flag,
            'transfer_event_flag': transfer_event_flag
        }

    def generate_env_telemetry(
        self,
        timestamp: datetime,
        sensor_id: str,
        outdoor_temp_c: float,
        hvac_status: str
    ) -> Dict:
        """
        Generate environmental sensor telemetry.

        Args:
            timestamp: Current time
            sensor_id: Sensor identifier
            outdoor_temp_c: Outdoor temperature
            hvac_status: HVAC status

        Returns:
            Dictionary of telemetry values
        """
        # Indoor temperature (affected by HVAC)
        target_temp = 24.0  # Data center target

        if hvac_status == 'running':
            indoor_temp = target_temp + np.random.normal(0, 1.0)
        elif hvac_status == 'degraded':
            indoor_temp = target_temp + np.random.normal(2.0, 3.0)
        else:  # fault
            # Temperature drifts toward outdoor
            indoor_temp = target_temp + (outdoor_temp_c - target_temp) * 0.5
            indoor_temp += np.random.normal(0, 2.0)

        # Humidity (from environment model)
        humidity = self.env_model.generate_humidity(
            timestamp,
            indoor_temp
        )

        return {
            'ts': timestamp,
            'sensor_id': sensor_id,
            'temperature_c': round(indoor_temp, 1),
            'humidity_pct': round(humidity, 1),
            'hvac_status': hvac_status
        }

    def simulate_time_step(
        self,
        timestamp: datetime,
        delta_time_hours: float,
        grid_available: bool,
        scheduled_equalize: bool,
        outdoor_temp_c: float,
        hvac_status: str,
        load_factor: float = 0.8
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Simulate one time step and generate telemetry.

        Args:
            timestamp: Current time
            delta_time_hours: Time step size
            grid_available: Grid power status
            scheduled_equalize: Equalization scheduled
            outdoor_temp_c: Outdoor temperature
            hvac_status: HVAC status
            load_factor: Load factor

        Returns:
            Tuple of (jar_telemetry_list, string_telemetry_list, env_telemetry)
        """
        # Determine operating mode
        mode = self.determine_mode(timestamp, grid_available, scheduled_equalize)

        # Generate string current
        string_current = self.generate_string_current(mode, timestamp, load_factor)

        # Update SOC
        self.update_soc(string_current, delta_time_hours)

        # Get indoor temperature (approximate from outdoor and HVAC)
        target_temp = 24.0
        if hvac_status == 'running':
            indoor_temp = target_temp + np.random.normal(0, 1.0)
        elif hvac_status == 'degraded':
            indoor_temp = target_temp + np.random.normal(2.0, 3.0)
        else:
            indoor_temp = target_temp + (outdoor_temp_c - target_temp) * 0.5

        # Update battery degradation models
        for battery_id, model in self.battery_models.items():
            # Calendar aging
            avg_voltage = self.FLOAT_VOLTAGE_TARGET if mode == 'float' else 13.9
            model.update_calendar_aging(
                delta_time_hours,
                indoor_temp,
                avg_voltage
            )

            # Cycle aging (if discharging)
            if string_current < 0:
                ah_throughput = abs(string_current * delta_time_hours)
                dod_pct = 100 - self.current_soc[battery_id]
                model.update_cycle_aging(ah_throughput, dod_pct, indoor_temp)

            # Check for sudden failure
            model.check_sudden_failure(timestamp)

        # Generate jar telemetry for all batteries
        jar_telemetry = []
        battery_voltages = []

        for battery_id in self.battery_models.keys():
            jar_data = self.generate_jar_telemetry(
                timestamp,
                battery_id,
                string_current,
                indoor_temp,
                mode
            )
            jar_telemetry.append(jar_data)
            battery_voltages.append(jar_data['voltage_v'])

        # Generate string telemetry
        string_telemetry = []
        for _, string_row in self.string_info.iterrows():
            string_data = self.generate_string_telemetry(
                timestamp,
                string_row['string_id'],
                string_current,
                mode,
                battery_voltages
            )
            string_telemetry.append(string_data)

        # Update mode state
        self.current_mode = mode

        return jar_telemetry, string_telemetry

    def generate_timeseries(
        self,
        start_date: datetime,
        end_date: datetime,
        sampling_interval_seconds: int = 5,
        outage_events: List[Tuple[datetime, datetime]] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate complete telemetry time series.

        Args:
            start_date: Simulation start
            end_date: Simulation end
            sampling_interval_seconds: Telemetry sampling rate
            outage_events: List of (start, end) tuples for power outages

        Returns:
            Tuple of (jar_telemetry_df, string_telemetry_df)
        """
        print(f"Generating telemetry from {start_date} to {end_date}...")
        print(f"  Sampling interval: {sampling_interval_seconds}s")

        jar_telemetry_list = []
        string_telemetry_list = []

        current_time = start_date
        delta_hours = sampling_interval_seconds / 3600.0

        # Initialize environmental state
        outdoor_temp = self.env_model.generate_ambient_temperature(current_time)
        hvac_status = 'running'

        # Equalization schedule (quarterly)
        equalize_dates = self._generate_equalization_schedule(start_date, end_date)

        step_count = 0
        total_steps = int((end_date - start_date).total_seconds() / sampling_interval_seconds)

        while current_time < end_date:
            # Update environmental conditions (every hour)
            if step_count % (3600 // sampling_interval_seconds) == 0:
                outdoor_temp = self.env_model.generate_ambient_temperature(
                    current_time,
                    outdoor_temp
                )
                hvac_status, _ = self.env_model.simulate_hvac_status(
                    current_time,
                    hvac_status,
                    outdoor_temp
                )

            # Check grid status
            grid_available = True
            if outage_events:
                for outage_start, outage_end in outage_events:
                    if outage_start <= current_time < outage_end:
                        grid_available = False
                        break

            # Check equalization schedule
            scheduled_equalize = any(
                eq_date <= current_time < eq_date + timedelta(hours=8)
                for eq_date in equalize_dates
            )

            # Load factor
            load_factor = self.env_model.get_load_profile(current_time)

            # Simulate time step
            jar_data, string_data = self.simulate_time_step(
                current_time,
                delta_hours,
                grid_available,
                scheduled_equalize,
                outdoor_temp,
                hvac_status,
                load_factor
            )

            jar_telemetry_list.extend(jar_data)
            string_telemetry_list.extend(string_data)

            current_time += timedelta(seconds=sampling_interval_seconds)
            step_count += 1

            if step_count % 10000 == 0:
                progress = (step_count / total_steps) * 100
                print(f"  Progress: {progress:.1f}% ({step_count}/{total_steps} steps)")

        jar_df = pd.DataFrame(jar_telemetry_list)
        string_df = pd.DataFrame(string_telemetry_list)

        print(f"Telemetry generation complete:")
        print(f"  Jar telemetry: {len(jar_df):,} records")
        print(f"  String telemetry: {len(string_df):,} records")

        return jar_df, string_df

    def _generate_equalization_schedule(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """Generate quarterly equalization schedule."""
        equalize_dates = []
        current = start_date

        while current < end_date:
            # Every 90 days, at 2 AM
            equalize_dates.append(current.replace(hour=2, minute=0, second=0))
            current += timedelta(days=90)

        return equalize_dates
