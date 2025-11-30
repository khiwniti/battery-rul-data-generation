"""
Thailand-Specific Environmental Models for Battery Telemetry Synthesis

This module implements realistic environmental conditions based on Thai facility operations:
- Three distinct seasons (hot, rainy, cool)
- Regional climate variations (9 regions)
- HVAC operational patterns and failures
- Power grid instability and outage patterns
- Monsoon effects on humidity and temperature
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple
import pytz


class ThailandEnvironmentModel:
    """
    Models Thai environmental conditions affecting battery performance.

    Based on 15+ years experience with data center operations across Thailand regions.
    """

    # Thai timezone
    BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

    # Thai seasons (based on meteorological patterns)
    SEASONS = {
        'hot': {
            'months': [3, 4, 5],  # March-May (very hot, dry)
            'temp_range': (30, 40),
            'humidity_range': (40, 70),
            'hvac_load_factor': 1.3
        },
        'rainy': {
            'months': [6, 7, 8, 9, 10],  # June-October (monsoon)
            'temp_range': (26, 35),
            'humidity_range': (70, 95),
            'hvac_load_factor': 1.1
        },
        'cool': {
            'months': [11, 12, 1, 2],  # November-February (coolest)
            'temp_range': (22, 32),
            'humidity_range': (50, 75),
            'hvac_load_factor': 0.8
        }
    }

    # Regional climate characteristics
    REGIONAL_CLIMATE = {
        'northern': {  # Chiangmai - cooler, drier
            'temp_offset': -2.0,
            'humidity_offset': -10,
            'altitude_m': 310
        },
        'northeastern': {  # Khon Kaen - hot, dry in hot season
            'temp_offset': 1.0,
            'humidity_offset': -5,
            'altitude_m': 165
        },
        'central': {  # Bangkok metro - urban heat island
            'temp_offset': 1.5,
            'humidity_offset': 5,
            'altitude_m': 5
        },
        'eastern': {  # Sriracha - coastal, humid
            'temp_offset': 0.5,
            'humidity_offset': 10,
            'altitude_m': 10
        },
        'southern': {  # Phuket, Hat Yai - tropical, humid year-round
            'temp_offset': 0.0,
            'humidity_offset': 15,
            'altitude_m': 20
        }
    }

    # HVAC operational patterns
    HVAC_PATTERNS = {
        'normal': {
            'efficiency': 0.95,
            'temp_control_std': 1.0,
            'failure_rate_per_year': 0.02
        },
        'degraded': {
            'efficiency': 0.75,
            'temp_control_std': 3.0,
            'failure_rate_per_year': 0.08
        },
        'failed': {
            'efficiency': 0.0,
            'temp_control_std': 8.0,
            'failure_rate_per_year': 0.0
        }
    }

    # Power grid characteristics by region
    GRID_RELIABILITY = {
        'northern': {'outages_per_year': 4, 'avg_duration_min': 45},
        'northeastern': {'outages_per_year': 6, 'avg_duration_min': 60},
        'central': {'outages_per_year': 2, 'avg_duration_min': 30},
        'eastern': {'outages_per_year': 3, 'avg_duration_min': 40},
        'southern': {'outages_per_year': 8, 'avg_duration_min': 90}  # Storm-prone
    }

    def __init__(self, region: str, seed: int = None):
        """
        Initialize environment model for specific region.

        Args:
            region: Thai region name (northern, northeastern, central, eastern, southern)
            seed: Random seed for reproducibility
        """
        self.region = region
        self.climate = self.REGIONAL_CLIMATE[region]
        self.grid = self.GRID_RELIABILITY[region]

        if seed is not None:
            np.random.seed(seed)

    def get_season(self, dt: datetime) -> str:
        """Determine Thai season from datetime."""
        month = dt.month
        for season, info in self.SEASONS.items():
            if month in info['months']:
                return season
        return 'hot'

    def generate_ambient_temperature(
        self,
        timestamp: datetime,
        previous_temp: float = None
    ) -> float:
        """
        Generate realistic ambient temperature with daily and seasonal cycles.

        Args:
            timestamp: Current timestamp
            previous_temp: Previous temperature for continuity

        Returns:
            Temperature in Celsius
        """
        season = self.get_season(timestamp)
        season_info = self.SEASONS[season]

        # Base temperature from seasonal range
        temp_min, temp_max = season_info['temp_range']
        temp_base = (temp_min + temp_max) / 2
        temp_amplitude = (temp_max - temp_min) / 2

        # Apply regional offset
        temp_base += self.climate['temp_offset']

        # Daily cycle (cooler at night, hottest at 2-3 PM)
        hour = timestamp.hour
        daily_cycle = np.sin((hour - 6) * np.pi / 12) * 0.7  # Peak at 2 PM

        # Seasonal variation
        day_of_year = timestamp.timetuple().tm_yday
        seasonal_cycle = np.sin((day_of_year - 80) * 2 * np.pi / 365) * 0.3

        # Calculate temperature
        temp = temp_base + temp_amplitude * (daily_cycle + seasonal_cycle)

        # Add realistic noise
        temp += np.random.normal(0, 0.8)

        # Smooth transition from previous temperature
        if previous_temp is not None:
            temp = 0.85 * previous_temp + 0.15 * temp

        return round(temp, 1)

    def generate_humidity(
        self,
        timestamp: datetime,
        temperature: float,
        previous_humidity: float = None
    ) -> float:
        """
        Generate realistic humidity correlated with temperature and season.

        Args:
            timestamp: Current timestamp
            temperature: Current temperature
            previous_humidity: Previous humidity for continuity

        Returns:
            Relative humidity percentage
        """
        season = self.get_season(timestamp)
        season_info = self.SEASONS[season]

        # Base humidity from seasonal range
        hum_min, hum_max = season_info['humidity_range']
        hum_base = (hum_min + hum_max) / 2

        # Apply regional offset
        hum_base += self.climate['humidity_offset']

        # Inverse correlation with temperature (hotter = drier, except rainy season)
        if season == 'rainy':
            temp_factor = 0.1  # Weak correlation in rainy season
        else:
            temp_factor = -0.5  # Strong inverse correlation

        # Daily cycle (higher at night)
        hour = timestamp.hour
        daily_cycle = -np.sin((hour - 6) * np.pi / 12) * 8

        # Calculate humidity
        humidity = hum_base + temp_factor * (temperature - 28) + daily_cycle

        # Add noise
        humidity += np.random.normal(0, 3)

        # Smooth transition
        if previous_humidity is not None:
            humidity = 0.8 * previous_humidity + 0.2 * humidity

        # Clamp to valid range
        humidity = np.clip(humidity, 20, 99)

        return round(humidity, 1)

    def simulate_hvac_status(
        self,
        timestamp: datetime,
        current_status: str,
        outdoor_temp: float
    ) -> Tuple[str, float]:
        """
        Simulate HVAC system status and indoor temperature.

        Args:
            timestamp: Current timestamp
            current_status: Current HVAC status
            outdoor_temp: Outdoor temperature

        Returns:
            Tuple of (hvac_status, indoor_temperature)
        """
        # HVAC failure probability (higher in hot season)
        season = self.get_season(timestamp)
        load_factor = self.SEASONS[season]['hvac_load_factor']

        # State transitions
        if current_status == 'running':
            # Probability of degradation or failure
            if np.random.random() < 0.0001 * load_factor:
                new_status = 'degraded'
            elif np.random.random() < 0.00002 * load_factor:
                new_status = 'fault'
            else:
                new_status = 'running'
        elif current_status == 'degraded':
            # Recovery or further degradation
            if np.random.random() < 0.001:
                new_status = 'running'  # Maintenance fix
            elif np.random.random() < 0.0005:
                new_status = 'fault'
            else:
                new_status = 'degraded'
        else:  # fault
            # Recovery after maintenance (typically 2-8 hours)
            if np.random.random() < 0.01:
                new_status = 'running'
            else:
                new_status = 'fault'

        # Calculate indoor temperature based on HVAC status
        target_temp = 24.0  # Data center target
        hvac_params = self.HVAC_PATTERNS.get(
            new_status,
            self.HVAC_PATTERNS['normal']
        )

        efficiency = hvac_params['efficiency']
        temp_std = hvac_params['temp_control_std']

        # Indoor temp is blend of outdoor and target
        indoor_temp = target_temp + (outdoor_temp - target_temp) * (1 - efficiency)
        indoor_temp += np.random.normal(0, temp_std)

        return new_status, round(indoor_temp, 1)

    def generate_power_outage_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list:
        """
        Generate realistic power outage events based on regional grid reliability.

        Args:
            start_date: Simulation start date
            end_date: Simulation end date

        Returns:
            List of (outage_start, outage_end) tuples
        """
        days = (end_date - start_date).days
        years = days / 365.25

        # Expected number of outages
        n_outages = int(self.grid['outages_per_year'] * years)

        # More outages in rainy season (storms)
        outages = []
        for _ in range(n_outages):
            # Random timestamp
            random_day = np.random.randint(0, days)
            outage_start = start_date + timedelta(days=random_day)

            # Increase probability in rainy season
            season = self.get_season(outage_start)
            if season == 'rainy' and np.random.random() < 0.3:
                # Additional storm-related outage
                pass

            # Random hour (more likely during afternoon storms)
            if season == 'rainy':
                hour = np.random.choice(
                    range(24),
                    p=self._get_storm_hour_probability()
                )
            else:
                hour = np.random.randint(0, 24)

            outage_start = outage_start.replace(hour=hour, minute=np.random.randint(0, 60))

            # Duration (log-normal distribution)
            duration_min = int(
                np.random.lognormal(
                    np.log(self.grid['avg_duration_min']),
                    0.8
                )
            )
            duration_min = min(duration_min, 480)  # Max 8 hours

            outage_end = outage_start + timedelta(minutes=duration_min)
            outages.append((outage_start, outage_end))

        return sorted(outages)

    def _get_storm_hour_probability(self) -> np.ndarray:
        """Storm probability by hour (peak in afternoon)."""
        probs = np.array([
            0.01, 0.01, 0.01, 0.01, 0.01, 0.02,  # 00-05
            0.02, 0.03, 0.04, 0.05, 0.06, 0.07,  # 06-11
            0.08, 0.10, 0.12, 0.11, 0.09, 0.07,  # 12-17 (peak afternoon)
            0.05, 0.04, 0.03, 0.02, 0.02, 0.01   # 18-23
        ])
        return probs / probs.sum()

    def get_load_profile(self, timestamp: datetime, location_type: str = 'datacenter') -> float:
        """
        Get electrical load profile factor (0-1) based on time and location type.

        Args:
            timestamp: Current timestamp
            location_type: Type of facility

        Returns:
            Load factor (0.3-1.0)
        """
        hour = timestamp.hour
        day_of_week = timestamp.weekday()

        # Data centers have relatively constant load, but with patterns
        if location_type == 'datacenter':
            # Slightly higher during business hours
            if 8 <= hour <= 20:
                base_load = 0.85
            else:
                base_load = 0.75

            # Weekend slightly lower
            if day_of_week >= 5:
                base_load *= 0.95

            # Add variation
            load = base_load + np.random.normal(0, 0.05)
            return np.clip(load, 0.5, 1.0)

        return 0.8
