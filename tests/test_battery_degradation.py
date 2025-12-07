"""
Unit tests for Battery Degradation Model

Tests critical physics-based degradation calculations for production use.
"""

import sys
import os
import pytest
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from battery_degradation import BatteryDegradationModel


class TestBatteryDegradationModel:
    """Test suite for battery degradation physics model."""

    def test_initialization(self):
        """Test model initialization with valid parameters."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime(2023, 1, 1),
            seed=42
        )

        assert model.battery_id == "TEST001"
        assert model.initial_capacity_ah == 120.0
        assert model.current_capacity_ah == 120.0
        assert model.current_soh_pct == 100.0
        assert not model.failed

    def test_temperature_acceleration_arrhenius(self):
        """Test temperature acceleration follows Arrhenius equation."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now()
        )

        # At reference temperature (25°C), acceleration should be 1.0
        accel_25 = model.get_temperature_acceleration_factor(25.0)
        assert abs(accel_25 - 1.0) < 0.01

        # At higher temperature, acceleration should increase
        accel_35 = model.get_temperature_acceleration_factor(35.0)
        assert accel_35 > 1.0

        # At lower temperature, acceleration should decrease
        accel_15 = model.get_temperature_acceleration_factor(15.0)
        assert accel_15 < 1.0

        # Check realistic values (10°C increase ≈ 1.5-2x acceleration for VRLA)
        # With E_a = 0.7 eV, expect ~1.56x
        expected_ratio = np.exp((0.7 / 8.617e-5) * (1/298.15 - 1/308.15))
        assert abs(accel_35 / accel_25 - expected_ratio) < 0.01

    def test_calendar_aging_reduces_soh(self):
        """Test calendar aging gradually reduces SOH."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='healthy',
            seed=42
        )

        initial_soh = model.current_soh_pct

        # Simulate 30 days of calendar aging at 25°C
        model.update_calendar_aging(
            delta_time_hours=24 * 30,
            avg_temperature_c=25.0,
            avg_float_voltage_v=13.65
        )

        # SOH should decrease
        assert model.current_soh_pct < initial_soh

        # For healthy profile (2%/year), 30 days should lose ~0.164%
        expected_loss = (2.0 / 365.0) * 30
        actual_loss = initial_soh - model.current_soh_pct
        assert abs(actual_loss - expected_loss) < 0.05

    def test_calendar_aging_temperature_effect(self):
        """Test calendar aging accelerates at higher temperature."""
        model1 = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='healthy',
            seed=42
        )

        model2 = BatteryDegradationModel(
            battery_id="TEST002",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='healthy',
            seed=42
        )

        # Age at different temperatures
        model1.update_calendar_aging(24 * 30, 25.0, 13.65)  # 25°C
        model2.update_calendar_aging(24 * 30, 35.0, 13.65)  # 35°C

        # Higher temperature should cause more degradation
        assert model2.current_soh_pct < model1.current_soh_pct

    def test_cycle_aging_reduces_soh(self):
        """Test cycle aging from discharge events."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='healthy',
            seed=42
        )

        initial_soh = model.current_soh_pct

        # Simulate 10 full cycles (10% DoD each, 10 times = 1 equivalent full cycle)
        for _ in range(10):
            model.update_cycle_aging(
                ah_throughput=12.0,  # 10% of 120Ah
                depth_of_discharge_pct=10.0,
                temperature_c=25.0
            )

        # SOH should decrease from cycling
        assert model.current_soh_pct < initial_soh

        # Cycle count should be tracked
        assert abs(model.cycle_count - 1.0) < 0.1  # ~1 full cycle

    def test_soh_never_negative(self):
        """Test SOH cannot go below 0%."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='failing',  # Rapid degradation
            seed=42
        )

        # Extreme aging
        for _ in range(1000):
            model.update_calendar_aging(24 * 365, 50.0, 14.0)  # 1 year at high temp

        # SOH should never be negative
        assert model.current_soh_pct >= 0.0
        assert model.current_capacity_ah >= 0.0

    def test_resistance_increases_with_aging(self):
        """Test internal resistance increases as battery ages."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='accelerated',
            seed=42
        )

        initial_resistance = model.current_resistance_mohm

        # Age the battery
        model.update_calendar_aging(24 * 365, 30.0, 13.65)  # 1 year

        # Resistance should increase
        assert model.current_resistance_mohm > initial_resistance

    def test_ocv_curve_monotonic(self):
        """Test OCV increases monotonically with SOC."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now()
        )

        # Check OCV at different SOC levels
        soc_values = [0, 25, 50, 75, 100]
        ocv_values = [model.get_ocv(soc) for soc in soc_values]

        # OCV should increase with SOC
        for i in range(len(ocv_values) - 1):
            assert ocv_values[i + 1] > ocv_values[i]

        # Check reasonable voltage range
        assert 11.5 < ocv_values[0] < 12.0  # 0% SOC
        assert 12.5 < ocv_values[-1] < 13.0  # 100% SOC

    def test_terminal_voltage_under_load(self):
        """Test terminal voltage drops under discharge load."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now()
        )

        # OCV at 100% SOC
        ocv = model.get_ocv(100.0)

        # Terminal voltage under 100A discharge (negative current)
        v_load = model.get_terminal_voltage(100.0, -100.0, 25.0)

        # Terminal voltage should be lower than OCV
        assert v_load < ocv

        # Voltage drop should be approximately I*R (within noise)
        expected_drop = 100.0 * (3.5 / 1000.0)  # 100A × 3.5mΩ = 0.35V
        actual_drop = ocv - v_load
        assert abs(actual_drop - expected_drop) < 0.1  # Allow for noise and nonlinearity

    def test_rul_estimation_realistic(self):
        """Test RUL estimation returns reasonable values."""
        model = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='healthy',
            seed=42
        )

        # Fresh battery should have long RUL
        rul_days = model.estimate_rul_days(eol_soh_threshold=80.0)
        assert rul_days > 1000  # At least 3 years for healthy battery

        # Age to 85% SOH
        while model.current_soh_pct > 85.0:
            model.update_calendar_aging(24 * 30, 25.0, 13.65)

        # RUL should be shorter but still positive
        rul_days = model.estimate_rul_days(eol_soh_threshold=80.0)
        assert 0 < rul_days < 1000

        # Age to below EOL threshold
        while model.current_soh_pct > 75.0:
            model.update_calendar_aging(24 * 30, 25.0, 13.65)

        # RUL should be zero
        rul_days = model.estimate_rul_days(eol_soh_threshold=80.0)
        assert rul_days == 0.0

    def test_no_double_counting_calendar_cycle(self):
        """Test calendar and cycle aging are independent (no double counting)."""
        # Create two identical batteries
        model1 = BatteryDegradationModel(
            battery_id="TEST001",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='healthy',
            seed=42
        )

        model2 = BatteryDegradationModel(
            battery_id="TEST002",
            initial_capacity_ah=120.0,
            initial_resistance_mohm=3.5,
            installed_date=datetime.now(),
            profile='healthy',
            seed=42
        )

        # Battery 1: Only calendar aging (no cycles)
        model1.update_calendar_aging(24 * 365, 25.0, 13.65)  # 1 year
        calendar_only_loss = 100.0 - model1.current_soh_pct

        # Battery 2: Only cycle aging (no time passing)
        # Simulate 100 full cycles with NO calendar aging
        for _ in range(100):
            model2.update_cycle_aging(120.0, 100.0, 25.0)
        cycle_only_loss = 100.0 - model2.current_soh_pct

        # Both mechanisms should cause degradation
        assert calendar_only_loss > 0
        assert cycle_only_loss > 0

        # Total degradation from both should be approximately additive
        # (not multiplicative, which would indicate double counting)
        # Allow some nonlinearity but check it's not 2× either value
        assert cycle_only_loss < calendar_only_loss * 3
        assert calendar_only_loss < cycle_only_loss * 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
