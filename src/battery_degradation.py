"""
VRLA Battery Degradation Model

Realistic battery aging simulation based on:
- Electrochemical degradation mechanisms
- Temperature acceleration (Arrhenius)
- Cycling stress
- Float voltage stress
- Thai environmental conditions
- Calendar aging

Based on 15+ years of field data from Thai data centers.
"""

import numpy as np
from typing import Dict, Tuple
from datetime import datetime, timedelta


class BatteryDegradationModel:
    """
    Physics-based VRLA battery degradation model.

    Simulates:
    - State of Health (SOH) decline
    - Internal resistance increase
    - Capacity fade
    - Sudden failure events
    """

    # Degradation profiles matching real-world observations
    PROFILES = {
        'healthy': {
            'soh_decline_pct_per_year': 2.0,  # Normal aging
            'resistance_increase_pct_per_year': 5.0,
            'cycle_stress_factor': 1.0,
            'temp_acceleration_factor': 1.0,
            'sudden_failure_probability': 0.0001,
            'description': '85% of fleet - normal operation'
        },
        'accelerated': {
            'soh_decline_pct_per_year': 8.0,  # Accelerated aging
            'resistance_increase_pct_per_year': 15.0,
            'cycle_stress_factor': 1.5,
            'temp_acceleration_factor': 1.3,
            'sudden_failure_probability': 0.001,
            'description': '12% of fleet - higher stress conditions'
        },
        'failing': {
            'soh_decline_pct_per_year': 25.0,  # End of life
            'resistance_increase_pct_per_year': 40.0,
            'cycle_stress_factor': 2.0,
            'temp_acceleration_factor': 1.5,
            'sudden_failure_probability': 0.01,
            'description': '3% of fleet - approaching failure'
        }
    }

    # Fleet distribution
    PROFILE_DISTRIBUTION = {
        'healthy': 0.85,
        'accelerated': 0.12,
        'failing': 0.03
    }

    # Temperature acceleration (Arrhenius equation)
    TEMP_REFERENCE_C = 25.0  # Reference temperature
    ACTIVATION_ENERGY_EV = 0.7  # Typical for VRLA

    # Cycling stress parameters
    DOD_STRESS_EXPONENT = 2.0  # Deeper discharge = more stress
    CYCLE_BASE_CAPACITY_LOSS_PCT = 0.001  # Per equivalent full cycle

    def __init__(
        self,
        battery_id: str,
        initial_capacity_ah: float,
        initial_resistance_mohm: float,
        installed_date: datetime,
        profile: str = None,
        seed: int = None
    ):
        """
        Initialize battery degradation model.

        Args:
            battery_id: Unique battery identifier
            initial_capacity_ah: Initial capacity
            initial_resistance_mohm: Initial internal resistance
            installed_date: Installation date
            profile: Degradation profile ('healthy', 'accelerated', 'failing')
            seed: Random seed
        """
        self.battery_id = battery_id
        self.initial_capacity_ah = initial_capacity_ah
        self.initial_resistance_mohm = initial_resistance_mohm
        self.installed_date = installed_date

        # Assign degradation profile
        if profile is None:
            profile = np.random.choice(
                list(self.PROFILE_DISTRIBUTION.keys()),
                p=list(self.PROFILE_DISTRIBUTION.values())
            )
        self.profile = self.PROFILES[profile]
        self.profile_name = profile

        # State variables
        self.current_capacity_ah = initial_capacity_ah
        self.current_resistance_mohm = initial_resistance_mohm
        self.current_soh_pct = 100.0
        self.cumulative_ah_throughput = 0.0
        self.cycle_count = 0
        self.failed = False
        self.failure_date = None
        self.failure_mode = None

        # Degradation tracking
        self.calendar_age_days = 0
        self.temperature_stress_accumulated = 0.0
        self.cycle_stress_accumulated = 0.0

        if seed is not None:
            np.random.seed(seed)

    def get_temperature_acceleration_factor(self, temperature_c: float) -> float:
        """
        Calculate temperature acceleration factor using Arrhenius equation.

        Higher temperature = faster aging
        """
        T_ref = self.TEMP_REFERENCE_C + 273.15  # Kelvin
        T = temperature_c + 273.15  # Kelvin

        k_B = 8.617e-5  # Boltzmann constant (eV/K)
        E_a = self.ACTIVATION_ENERGY_EV

        acceleration = np.exp((E_a / k_B) * (1/T_ref - 1/T))

        return acceleration

    def update_calendar_aging(
        self,
        delta_time_hours: float,
        avg_temperature_c: float,
        avg_float_voltage_v: float
    ):
        """
        Update calendar aging (time-based degradation).

        Calendar aging represents time-dependent degradation mechanisms:
        - Grid corrosion
        - Electrolyte dry-out
        - Self-discharge
        - SEI layer growth

        This is INDEPENDENT from cycle aging and both contribute to total SOH loss.

        Args:
            delta_time_hours: Time elapsed
            avg_temperature_c: Average temperature during period
            avg_float_voltage_v: Average float voltage
        """
        delta_days = delta_time_hours / 24.0
        self.calendar_age_days += delta_days

        # Temperature acceleration
        temp_accel = self.get_temperature_acceleration_factor(avg_temperature_c)
        temp_accel *= self.profile['temp_acceleration_factor']

        # Voltage stress (higher voltage = faster corrosion)
        voltage_stress = 1.0
        if avg_float_voltage_v > 13.70:  # Above optimal
            voltage_stress = 1.0 + (avg_float_voltage_v - 13.70) * 0.5
        elif avg_float_voltage_v < 13.50:  # Below optimal (sulfation)
            voltage_stress = 1.0 + (13.50 - avg_float_voltage_v) * 0.3

        # Calculate aging rate
        base_aging_rate = self.profile['soh_decline_pct_per_year'] / 365.0  # Per day
        actual_aging_rate = base_aging_rate * temp_accel * voltage_stress

        # Update SOH
        soh_loss = actual_aging_rate * delta_days
        self.current_soh_pct = max(0, self.current_soh_pct - soh_loss)
        self.current_capacity_ah = self.initial_capacity_ah * (self.current_soh_pct / 100.0)

        # Update resistance (increases with aging)
        base_resistance_rate = self.profile['resistance_increase_pct_per_year'] / 365.0
        actual_resistance_rate = base_resistance_rate * temp_accel * voltage_stress

        resistance_increase = actual_resistance_rate * delta_days
        resistance_multiplier = 1 + (resistance_increase / 100.0)
        self.current_resistance_mohm *= resistance_multiplier

        # Accumulate temperature stress
        self.temperature_stress_accumulated += (avg_temperature_c - self.TEMP_REFERENCE_C) * delta_days

    def update_cycle_aging(
        self,
        ah_throughput: float,
        depth_of_discharge_pct: float,
        temperature_c: float
    ):
        """
        Update cycle aging (discharge/charge stress).

        Cycle aging represents stress-dependent degradation mechanisms:
        - Active material loss from expansion/contraction
        - Separator degradation
        - Electrolyte decomposition during cycling
        - Lithium plating (at high charge rates)

        This is INDEPENDENT from calendar aging and both contribute to total SOH loss.
        NO DOUBLE-COUNTING: Calendar aging runs continuously, cycle aging only during discharge.

        Args:
            ah_throughput: Ah discharged/charged
            depth_of_discharge_pct: DoD percentage
            temperature_c: Temperature during cycling
        """
        # Equivalent full cycles
        cycles = ah_throughput / self.initial_capacity_ah
        self.cycle_count += cycles
        self.cumulative_ah_throughput += ah_throughput

        # DoD stress (deeper discharge = more stress)
        dod_stress = (depth_of_discharge_pct / 100.0) ** self.DOD_STRESS_EXPONENT

        # Temperature stress during cycling
        temp_accel = self.get_temperature_acceleration_factor(temperature_c)

        # Cycle stress factor from profile
        cycle_factor = self.profile['cycle_stress_factor']

        # Calculate capacity loss from cycling
        capacity_loss_pct = (
            self.CYCLE_BASE_CAPACITY_LOSS_PCT *
            cycles *
            dod_stress *
            temp_accel *
            cycle_factor
        )

        self.current_soh_pct = max(0, self.current_soh_pct - capacity_loss_pct)
        self.current_capacity_ah = self.initial_capacity_ah * (self.current_soh_pct / 100.0)

        # Resistance increase from cycling
        resistance_increase_pct = capacity_loss_pct * 2.0  # Resistance increases faster
        self.current_resistance_mohm *= (1 + resistance_increase_pct / 100.0)

        # Accumulate cycle stress
        self.cycle_stress_accumulated += cycles * dod_stress

    def check_sudden_failure(self, current_time: datetime) -> bool:
        """
        Check for sudden failure event (thermal runaway, short circuit, etc.).

        Args:
            current_time: Current simulation time

        Returns:
            True if battery failed
        """
        if self.failed:
            return True

        # Base failure probability from profile
        failure_prob = self.profile['sudden_failure_probability']

        # Increased probability as SOH declines
        if self.current_soh_pct < 80:
            failure_prob *= 2.0
        if self.current_soh_pct < 60:
            failure_prob *= 3.0
        if self.current_soh_pct < 40:
            failure_prob *= 5.0

        # Random failure event
        if np.random.random() < failure_prob:
            self.failed = True
            self.failure_date = current_time
            self.current_soh_pct = 0.0

            # Determine failure mode
            failure_modes = [
                'thermal_runaway',
                'internal_short',
                'dry_out',
                'grid_corrosion',
                'sulfation'
            ]
            weights = [0.05, 0.10, 0.30, 0.35, 0.20]
            self.failure_mode = np.random.choice(failure_modes, p=weights)

            return True

        return False

    def get_state(self) -> Dict:
        """Get current battery state."""
        return {
            'battery_id': self.battery_id,
            'soh_pct': round(self.current_soh_pct, 2),
            'capacity_ah': round(self.current_capacity_ah, 2),
            'resistance_mohm': round(self.current_resistance_mohm, 3),
            'cycle_count': round(self.cycle_count, 2),
            'ah_throughput': round(self.cumulative_ah_throughput, 2),
            'calendar_age_days': round(self.calendar_age_days, 1),
            'failed': self.failed,
            'failure_date': self.failure_date,
            'failure_mode': self.failure_mode,
            'profile': self.profile_name
        }

    def get_ocv(self, soc_pct: float) -> float:
        """
        Get open-circuit voltage from SOC.

        Uses typical VRLA OCV curve.
        """
        # Normalized SOC (0-1)
        soc = np.clip(soc_pct / 100.0, 0.0, 1.0)

        # VRLA OCV curve (simplified polynomial)
        # At 25°C: 100% SOC ≈ 12.7V, 50% SOC ≈ 12.3V, 0% SOC ≈ 11.8V
        ocv = 11.8 + 0.9 * soc + 0.05 * (soc ** 3)

        # Adjust for SOH (degraded batteries have slightly lower OCV)
        soh_factor = 0.95 + 0.05 * (self.current_soh_pct / 100.0)
        ocv *= soh_factor

        return ocv

    def get_terminal_voltage(
        self,
        soc_pct: float,
        current_a: float,
        temperature_c: float
    ) -> float:
        """
        Calculate terminal voltage under load/charge.

        V_terminal = OCV - I * R_internal

        Args:
            soc_pct: State of charge
            current_a: Current (positive = charge, negative = discharge)
            temperature_c: Battery temperature

        Returns:
            Terminal voltage
        """
        ocv = self.get_ocv(soc_pct)

        # Temperature effect on resistance (increases at low temp)
        temp_factor = 1.0 + (25.0 - temperature_c) * 0.01
        effective_resistance_ohm = self.current_resistance_mohm * 0.001 * temp_factor

        # Voltage drop
        v_terminal = ocv - current_a * effective_resistance_ohm

        # Add measurement noise
        v_terminal += np.random.normal(0, 0.01)

        return round(v_terminal, 3)

    def estimate_rul_days(self, eol_soh_threshold: float = 80.0) -> float:
        """
        Estimate remaining useful life in days.

        Simple linear extrapolation based on current degradation rate.
        """
        if self.failed:
            return 0.0

        if self.current_soh_pct <= eol_soh_threshold:
            return 0.0

        # Calculate degradation rate (SOH % per day)
        if self.calendar_age_days > 0:
            degradation_rate = (100.0 - self.current_soh_pct) / self.calendar_age_days
        else:
            # Use profile base rate
            degradation_rate = self.profile['soh_decline_pct_per_year'] / 365.0

        if degradation_rate <= 0:
            return 9999.0  # Not degrading

        # Days until EOL
        soh_remaining = self.current_soh_pct - eol_soh_threshold
        rul_days = soh_remaining / degradation_rate

        return max(0.0, rul_days)
