"""
Battery Digital Twin - Equivalent Circuit Model (ECM)

This module implements a physics-based digital twin for VRLA batteries using:
- Equivalent Circuit Model (2RC ECM)
- Extended Kalman Filter (EKF) for state estimation
- Electrochemical degradation tracking
- Real-time SOC/SOH estimation

The Digital Twin runs in parallel with ML models to provide:
1. Physics-based state estimation (more accurate)
2. Real-time predictions without training data
3. Model fusion: Combine physics + ML predictions
"""

import numpy as np
from scipy.integrate import odeint
from scipy.optimize import minimize
from typing import Dict, Tuple
import pandas as pd


class BatteryECMDigitalTwin:
    """
    Battery Digital Twin using 2RC Equivalent Circuit Model.

    ECM Parameters:
    - R0: Ohmic resistance (instant voltage drop)
    - R1, C1: First RC pair (activation polarization)
    - R2, C2: Second RC pair (concentration polarization)
    - OCV(SOC): Open Circuit Voltage curve
    """

    def __init__(
        self,
        battery_id: str,
        nominal_capacity_ah: float = 120.0,
        nominal_voltage_v: float = 12.0,
        initial_soh: float = 100.0
    ):
        """
        Initialize Digital Twin.

        Args:
            battery_id: Battery unique identifier
            nominal_capacity_ah: Rated capacity (120 Ah for HX12-120)
            nominal_voltage_v: Nominal voltage (12V)
            initial_soh: Initial state of health (%)
        """
        self.battery_id = battery_id
        self.nominal_capacity_ah = nominal_capacity_ah
        self.nominal_voltage_v = nominal_voltage_v

        # State variables
        self.soc = 100.0  # State of Charge (%)
        self.soh = initial_soh  # State of Health (%)
        self.current_capacity_ah = nominal_capacity_ah * (initial_soh / 100.0)

        # ECM parameters (initial values for VRLA)
        self.R0 = 0.0035  # Ohm (3.5 mΩ)
        self.R1 = 0.0015  # Ohm (1.5 mΩ)
        self.C1 = 2000.0  # Farad (activation)
        self.R2 = 0.0010  # Ohm (1.0 mΩ)
        self.C2 = 5000.0  # Farad (concentration)

        # Internal states
        self.V1 = 0.0  # Voltage across C1
        self.V2 = 0.0  # Voltage across C2

        # Temperature
        self.temperature_c = 25.0

        # Degradation tracking
        self.cycle_count = 0
        self.ah_throughput = 0

        # Kalman filter state
        self.P = np.eye(3) * 0.1  # State covariance
        self.Q = np.eye(3) * 0.001  # Process noise
        self.R = np.array([[0.01]])  # Measurement noise

    def get_ocv(self, soc: float) -> float:
        """
        Open Circuit Voltage as function of SOC.

        Uses typical VRLA OCV curve.

        Args:
            soc: State of Charge (0-100%)

        Returns:
            OCV in Volts
        """
        soc_normalized = np.clip(soc / 100.0, 0.0, 1.0)

        # VRLA OCV curve (polynomial fit)
        # 100% SOC ≈ 12.7V, 50% SOC ≈ 12.3V, 0% SOC ≈ 11.8V
        ocv = (11.8 +
               0.9 * soc_normalized +
               0.05 * (soc_normalized ** 3))

        # Adjust for SOH (degraded batteries have lower OCV)
        ocv *= (0.95 + 0.05 * (self.soh / 100.0))

        return ocv

    def update_rc_states(self, current_a: float, dt: float):
        """
        Update RC circuit states (V1, V2) using state-space model.

        dV1/dt = (I - V1/(R1*C1)) / C1
        dV2/dt = (I - V2/(R2*C2)) / C2

        Args:
            current_a: Battery current (A, positive=charge)
            dt: Time step (seconds)
        """
        # Time constants
        tau1 = self.R1 * self.C1
        tau2 = self.R2 * self.C2

        # Exponential decay + current drive
        self.V1 = self.V1 * np.exp(-dt / tau1) + self.R1 * current_a * (1 - np.exp(-dt / tau1))
        self.V2 = self.V2 * np.exp(-dt / tau2) + self.R2 * current_a * (1 - np.exp(-dt / tau2))

    def get_terminal_voltage(self, current_a: float) -> float:
        """
        Calculate terminal voltage using ECM.

        V_terminal = OCV(SOC) - I*R0 - V1 - V2

        Args:
            current_a: Battery current (A, positive=charge, negative=discharge)

        Returns:
            Terminal voltage (V)
        """
        ocv = self.get_ocv(self.soc)

        # Temperature effect on resistance
        temp_factor = 1.0 + (25.0 - self.temperature_c) * 0.01
        R0_effective = self.R0 * temp_factor

        # ECM equation
        v_terminal = ocv - current_a * R0_effective - self.V1 - self.V2

        return v_terminal

    def update_soc(self, current_a: float, dt: float):
        """
        Update State of Charge using coulomb counting.

        Args:
            current_a: Battery current (A, positive=charge)
            dt: Time step (seconds)
        """
        # Coulomb counting
        ah_change = (current_a * dt) / 3600.0  # Convert to Ah

        # Coulombic efficiency (charge: 99%, discharge: 100%)
        if current_a > 0:
            ah_change *= 0.99

        # Update SOC
        soc_change = (ah_change / self.current_capacity_ah) * 100.0
        self.soc = np.clip(self.soc + soc_change, 0, 100)

        # Track throughput
        self.ah_throughput += abs(ah_change)
        if abs(ah_change) > 0.1:  # Count as cycle if >0.1 Ah
            self.cycle_count += abs(ah_change) / self.nominal_capacity_ah

    def update_soh(self, dt_hours: float, temperature_c: float):
        """
        Update State of Health based on aging mechanisms.

        Args:
            dt_hours: Time step in hours
            temperature_c: Temperature (°C)
        """
        # Calendar aging (capacity fade per hour)
        # 2% per year = 0.000228% per hour
        calendar_fade_rate = 0.00000228

        # Temperature acceleration (Arrhenius)
        temp_accel = np.exp(0.03 * (temperature_c - 25.0))

        # Cycling aging
        cycle_fade = self.cycle_count * 0.001  # 0.1% per 100 cycles

        # Update SOH
        calendar_fade = calendar_fade_rate * dt_hours * temp_accel * 100
        self.soh = max(0, self.soh - calendar_fade)

        # Update capacity
        self.current_capacity_ah = self.nominal_capacity_ah * (self.soh / 100.0)

        # Update ECM parameters (resistance increases with aging)
        soh_factor = self.soh / 100.0
        self.R0 = 0.0035 * (1.5 - 0.5 * soh_factor)  # Increase 50% at EOL
        self.R1 = 0.0015 * (1.5 - 0.5 * soh_factor)
        self.R2 = 0.0010 * (1.5 - 0.5 * soh_factor)

    def ekf_update(self, measured_voltage: float, current_a: float, dt: float):
        """
        Extended Kalman Filter for state estimation.

        State: [SOC, V1, V2]
        Measurement: Terminal Voltage

        Args:
            measured_voltage: Measured terminal voltage
            current_a: Measured current
            dt: Time step
        """
        # Current state
        x = np.array([self.soc, self.V1, self.V2])

        # State transition (prediction)
        soc_change = (current_a * dt / 3600.0) / self.current_capacity_ah * 100.0
        tau1 = self.R1 * self.C1
        tau2 = self.R2 * self.C2

        x_pred = np.array([
            x[0] + soc_change,
            x[1] * np.exp(-dt / tau1) + self.R1 * current_a * (1 - np.exp(-dt / tau1)),
            x[2] * np.exp(-dt / tau2) + self.R2 * current_a * (1 - np.exp(-dt / tau2))
        ])

        # Jacobian of state transition
        F = np.array([
            [1, 0, 0],
            [0, np.exp(-dt / tau1), 0],
            [0, 0, np.exp(-dt / tau2)]
        ])

        # Predict covariance
        P_pred = F @ self.P @ F.T + self.Q

        # Measurement prediction
        ocv_pred = self.get_ocv(x_pred[0])
        v_pred = ocv_pred - current_a * self.R0 - x_pred[1] - x_pred[2]

        # Measurement Jacobian
        docv_dsoc = 0.009  # Approximate derivative
        H = np.array([[docv_dsoc, -1, -1]])

        # Kalman gain
        S = H @ P_pred @ H.T + self.R
        K = (P_pred @ H.T / S[0, 0]).flatten()  # Flatten to 1D array

        # Update state
        innovation = measured_voltage - v_pred
        x_updated = x_pred + K * innovation

        # Update covariance
        K_col = K.reshape(-1, 1)  # Convert back to column vector for covariance update
        self.P = (np.eye(3) - np.outer(K_col, H)) @ P_pred

        # Store updated state
        self.soc = float(np.clip(x_updated[0], 0, 100))
        self.V1 = float(x_updated[1])
        self.V2 = float(x_updated[2])

    def predict_rul(self, eol_threshold: float = 80.0) -> float:
        """
        Predict Remaining Useful Life using physics-based degradation model.

        Args:
            eol_threshold: End-of-life SOH threshold (%)

        Returns:
            RUL in days
        """
        if self.soh <= eol_threshold:
            return 0.0

        # Estimate degradation rate from current conditions
        # 2% per year base, scaled by temperature and cycles
        base_rate = 2.0 / 365.0  # % per day

        temp_accel = np.exp(0.03 * (self.temperature_c - 25.0))

        # Cycling acceleration
        if self.cycle_count > 500:
            cycle_accel = 1.5
        elif self.cycle_count > 200:
            cycle_accel = 1.2
        else:
            cycle_accel = 1.0

        total_degradation_rate = base_rate * temp_accel * cycle_accel

        # Calculate RUL
        soh_remaining = self.soh - eol_threshold
        rul_days = soh_remaining / total_degradation_rate

        return max(0, rul_days)

    def step(
        self,
        measured_voltage: float,
        measured_current: float,
        temperature_c: float,
        dt: float,
        use_ekf: bool = True
    ) -> Dict:
        """
        Single time step update of Digital Twin.

        Args:
            measured_voltage: Measured terminal voltage (V)
            measured_current: Measured current (A, positive=charge)
            temperature_c: Temperature (°C)
            dt: Time step (seconds)
            use_ekf: Use EKF for state estimation (True) or simple update (False)

        Returns:
            Dictionary of Digital Twin state
        """
        self.temperature_c = temperature_c

        if use_ekf:
            # EKF-based state estimation
            self.ekf_update(measured_voltage, measured_current, dt)
        else:
            # Simple updates
            self.update_rc_states(measured_current, dt)
            self.update_soc(measured_current, dt)

        # Update SOH (slower time scale)
        self.update_soh(dt / 3600.0, temperature_c)

        # Get predictions
        predicted_voltage = self.get_terminal_voltage(measured_current)
        predicted_rul = self.predict_rul()

        return {
            'battery_id': self.battery_id,
            'soc': self.soc,
            'soh': self.soh,
            'capacity_ah': self.current_capacity_ah,
            'R0': self.R0,
            'R1': self.R1,
            'R2': self.R2,
            'C1': self.C1,
            'C2': self.C2,
            'V1': self.V1,
            'V2': self.V2,
            'predicted_voltage': predicted_voltage,
            'voltage_error': abs(measured_voltage - predicted_voltage),
            'rul_days': predicted_rul,
            'cycle_count': self.cycle_count,
            'ah_throughput': self.ah_throughput,
            'temperature_c': self.temperature_c
        }

    def get_state(self) -> Dict:
        """Get current Digital Twin state."""
        return {
            'battery_id': self.battery_id,
            'soc': self.soc,
            'soh': self.soh,
            'capacity_ah': self.current_capacity_ah,
            'R0': self.R0,
            'R1': self.R1,
            'R2': self.R2,
            'C1': self.C1,
            'C2': self.C2,
            'cycle_count': self.cycle_count,
            'ah_throughput': self.ah_throughput,
            'rul_days': self.predict_rul()
        }


class HybridPredictor:
    """
    Hybrid RUL Prediction combining Digital Twin (physics) + ML (data-driven).

    Fusion strategies:
    1. Weighted average
    2. Bayesian fusion
    3. Confidence-based selection
    """

    def __init__(self, digital_twin: BatteryECMDigitalTwin, ml_model=None):
        """
        Initialize hybrid predictor.

        Args:
            digital_twin: Physics-based Digital Twin
            ml_model: Trained ML model (optional)
        """
        self.digital_twin = digital_twin
        self.ml_model = ml_model

        # Fusion weights (can be learned)
        self.weight_dt = 0.6  # Digital Twin weight
        self.weight_ml = 0.4  # ML weight

    def predict_rul_weighted(
        self,
        ml_prediction: float = None,
        dt_confidence: float = 0.8,
        ml_confidence: float = 0.8
    ) -> Tuple[float, float]:
        """
        Fused RUL prediction using weighted average.

        Args:
            ml_prediction: ML model RUL prediction (days)
            dt_confidence: Digital Twin confidence (0-1)
            ml_confidence: ML model confidence (0-1)

        Returns:
            (fused_rul, confidence)
        """
        dt_rul = self.digital_twin.predict_rul()

        if ml_prediction is None or self.ml_model is None:
            # Only Digital Twin available
            return dt_rul, dt_confidence

        # Confidence-weighted fusion
        total_weight = dt_confidence + ml_confidence
        fused_rul = (dt_rul * dt_confidence + ml_prediction * ml_confidence) / total_weight

        # Combined confidence (geometric mean)
        combined_confidence = np.sqrt(dt_confidence * ml_confidence)

        return fused_rul, combined_confidence

    def predict_rul_bayesian(
        self,
        ml_prediction: float,
        dt_variance: float = 100.0,
        ml_variance: float = 100.0
    ) -> Tuple[float, float]:
        """
        Bayesian fusion of Digital Twin and ML predictions.

        Args:
            ml_prediction: ML prediction
            dt_variance: Digital Twin prediction variance
            ml_variance: ML prediction variance

        Returns:
            (fused_mean, fused_variance)
        """
        dt_rul = self.digital_twin.predict_rul()

        # Bayesian fusion (minimum variance estimator)
        fused_variance = 1 / (1/dt_variance + 1/ml_variance)
        fused_mean = fused_variance * (dt_rul/dt_variance + ml_prediction/ml_variance)

        return fused_mean, np.sqrt(fused_variance)

    def adaptive_fusion(
        self,
        ml_prediction: float,
        measured_voltage: float,
        predicted_voltage: float
    ) -> float:
        """
        Adaptive fusion based on Digital Twin accuracy.

        If DT voltage prediction is accurate, trust DT more.
        If DT has high error, trust ML more.

        Args:
            ml_prediction: ML RUL prediction
            measured_voltage: Actual measured voltage
            predicted_voltage: DT predicted voltage

        Returns:
            Fused RUL prediction
        """
        dt_rul = self.digital_twin.predict_rul()

        # Calculate DT voltage error
        voltage_error = abs(measured_voltage - predicted_voltage)

        # Adaptive weight (lower error = higher DT weight)
        # Error < 0.05V: weight_dt = 0.8
        # Error > 0.2V: weight_dt = 0.3
        if voltage_error < 0.05:
            weight_dt = 0.8
        elif voltage_error < 0.1:
            weight_dt = 0.65
        elif voltage_error < 0.2:
            weight_dt = 0.5
        else:
            weight_dt = 0.3

        weight_ml = 1 - weight_dt

        fused_rul = dt_rul * weight_dt + ml_prediction * weight_ml

        return fused_rul
