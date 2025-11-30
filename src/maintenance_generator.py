"""
Maintenance Event Generator

Generates realistic maintenance events based on Thai facility operational patterns:
- Monthly visual inspections and voltage measurements
- Quarterly thermal surveys (IR scans)
- Annual capacity tests
- Periodic impedance tests
- Corrective maintenance based on alerts
- Battery replacements
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import uuid


class MaintenanceEventGenerator:
    """Generate realistic maintenance events for Thai battery operations."""

    # Maintenance schedule (Thai data center practices)
    MAINTENANCE_SCHEDULE = {
        'visual_inspection': {
            'frequency_days': 30,
            'duration_hours': 2,
            'applies_to': 'location'
        },
        'voltage_measurement': {
            'frequency_days': 30,
            'duration_hours': 3,
            'applies_to': 'location'
        },
        'thermal_survey': {
            'frequency_days': 90,
            'duration_hours': 4,
            'applies_to': 'location'
        },
        'torque_check': {
            'frequency_days': 180,
            'duration_hours': 6,
            'applies_to': 'location'
        },
        'capacity_test': {
            'frequency_days': 365,
            'duration_hours': 8,
            'applies_to': 'string'
        },
        'impedance_test': {
            'frequency_days': 180,
            'duration_hours': 4,
            'applies_to': 'string'
        }
    }

    # Technician pool (Thai names)
    TECHNICIANS = [
        ('Somchai Srisawat', 'engineer'),
        ('Nattapong Wongsiri', 'engineer'),
        ('Siriporn Thongchai', 'engineer'),
        ('Wanchai Prasert', 'operator'),
        ('Supaporn Yamyong', 'operator'),
        ('Anan Chaiyaporn', 'operator')
    ]

    def __init__(self, seed: int = None):
        """Initialize maintenance event generator."""
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

        # Create technician IDs
        self.technician_ids = {
            name: uuid.uuid4() for name, _ in self.TECHNICIANS
        }

    def generate_scheduled_maintenance(
        self,
        start_date: datetime,
        end_date: datetime,
        locations: pd.DataFrame,
        batteries: pd.DataFrame,
        strings: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate scheduled maintenance events.

        Args:
            start_date: Simulation start
            end_date: Simulation end
            locations: Locations DataFrame
            batteries: Batteries DataFrame
            strings: Strings DataFrame

        Returns:
            DataFrame of maintenance events
        """
        print("Generating scheduled maintenance events...")

        events = []

        # Location-level maintenance
        for _, location in locations.iterrows():
            for event_type, schedule in self.MAINTENANCE_SCHEDULE.items():
                if schedule['applies_to'] != 'location':
                    continue

                current_date = start_date
                while current_date < end_date:
                    # Schedule maintenance (typically during business hours)
                    scheduled_time = current_date.replace(
                        hour=np.random.choice([9, 10, 11, 13, 14]),
                        minute=0,
                        second=0
                    )

                    # Completion time (with slight variation)
                    duration = schedule['duration_hours'] * np.random.uniform(0.9, 1.2)
                    completed_time = scheduled_time + timedelta(hours=duration)

                    # Assign technician
                    technician_name = np.random.choice([name for name, _ in self.TECHNICIANS])
                    technician_id = self.technician_ids[technician_name]

                    # Generate work order ID
                    work_order_id = f"WO-{scheduled_time.year}{scheduled_time.month:02d}-{np.random.randint(1000, 9999)}"

                    events.append({
                        'event_id': uuid.uuid4(),
                        'battery_id': None,
                        'string_id': None,
                        'location_id': location['location_id'],
                        'event_type': event_type,
                        'event_subtype': None,
                        'scheduled_date': scheduled_time,
                        'completed_date': completed_time,
                        'technician_id': technician_id,
                        'status': 'completed',
                        'work_order_id': work_order_id,
                        'notes': self._generate_maintenance_notes(event_type),
                        'photo_urls': [],
                        'ir_scan_url': f"s3://maintenance-photos/ir-{work_order_id}.jpg" if event_type == 'thermal_survey' else None,
                        'created_at': scheduled_time - timedelta(days=7),
                        'updated_at': completed_time
                    })

                    current_date += timedelta(days=schedule['frequency_days'])

        # String-level maintenance
        for _, string in strings.iterrows():
            for event_type, schedule in self.MAINTENANCE_SCHEDULE.items():
                if schedule['applies_to'] != 'string':
                    continue

                current_date = start_date
                while current_date < end_date:
                    scheduled_time = current_date.replace(
                        hour=np.random.choice([9, 10, 11, 13, 14]),
                        minute=0,
                        second=0
                    )

                    duration = schedule['duration_hours'] * np.random.uniform(0.9, 1.2)
                    completed_time = scheduled_time + timedelta(hours=duration)

                    technician_name = np.random.choice([name for name, _ in self.TECHNICIANS])
                    technician_id = self.technician_ids[technician_name]

                    work_order_id = f"WO-{scheduled_time.year}{scheduled_time.month:02d}-{np.random.randint(1000, 9999)}"

                    # Get location_id from string
                    location_id = None  # Would need to join through system->location

                    events.append({
                        'event_id': uuid.uuid4(),
                        'battery_id': None,
                        'string_id': string['string_id'],
                        'location_id': location_id,
                        'event_type': event_type,
                        'event_subtype': None,
                        'scheduled_date': scheduled_time,
                        'completed_date': completed_time,
                        'technician_id': technician_id,
                        'status': 'completed',
                        'work_order_id': work_order_id,
                        'notes': self._generate_maintenance_notes(event_type, string['string_code']),
                        'photo_urls': [],
                        'ir_scan_url': None,
                        'created_at': scheduled_time - timedelta(days=7),
                        'updated_at': completed_time
                    })

                    current_date += timedelta(days=schedule['frequency_days'])

        df = pd.DataFrame(events)
        print(f"  Generated {len(df):,} scheduled maintenance events")

        return df

    def generate_corrective_maintenance(
        self,
        batteries: pd.DataFrame,
        battery_degradation_states: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Generate corrective maintenance and battery replacements.

        Args:
            batteries: Batteries DataFrame
            battery_degradation_states: Dict of battery states at end of simulation
            start_date: Simulation start
            end_date: Simulation end

        Returns:
            DataFrame of corrective maintenance events
        """
        print("Generating corrective maintenance events...")

        events = []

        for battery_id, state in battery_degradation_states.items():
            # Battery replacement if failed or very degraded
            if state['failed'] or state['soh_pct'] < 60:
                # Schedule replacement
                if state['failed'] and state['failure_date']:
                    # Emergency replacement within 1-3 days of failure
                    replacement_date = state['failure_date'] + timedelta(days=np.random.randint(1, 4))
                else:
                    # Planned replacement based on monitoring
                    days_since_start = (end_date - start_date).days
                    replacement_day = np.random.randint(int(days_since_start * 0.7), days_since_start)
                    replacement_date = start_date + timedelta(days=replacement_day)

                if replacement_date < end_date:
                    scheduled_time = replacement_date.replace(
                        hour=np.random.choice([10, 11, 13, 14]),
                        minute=0
                    )

                    completed_time = scheduled_time + timedelta(hours=np.random.uniform(2, 4))

                    technician_name = np.random.choice([name for name, role in self.TECHNICIANS if role == 'engineer'])
                    technician_id = self.technician_ids[technician_name]

                    work_order_id = f"WO-{scheduled_time.year}{scheduled_time.month:02d}-{np.random.randint(1000, 9999)}"

                    failure_notes = f"Battery replacement. "
                    if state['failed']:
                        failure_notes += f"Failure mode: {state['failure_mode']}. "
                    failure_notes += f"Final SOH: {state['soh_pct']:.1f}%. "

                    events.append({
                        'event_id': uuid.uuid4(),
                        'battery_id': battery_id,
                        'string_id': None,
                        'location_id': None,
                        'event_type': 'replacement',
                        'event_subtype': state.get('failure_mode'),
                        'scheduled_date': scheduled_time,
                        'completed_date': completed_time,
                        'technician_id': technician_id,
                        'status': 'completed',
                        'work_order_id': work_order_id,
                        'notes': failure_notes,
                        'photo_urls': [f"s3://maintenance-photos/{work_order_id}-before.jpg",
                                     f"s3://maintenance-photos/{work_order_id}-after.jpg"],
                        'ir_scan_url': None,
                        'created_at': scheduled_time - timedelta(days=3),
                        'updated_at': completed_time
                    })

        df = pd.DataFrame(events)
        print(f"  Generated {len(df):,} corrective maintenance events")

        return df

    def _generate_maintenance_notes(self, event_type: str, asset_code: str = None) -> str:
        """Generate realistic maintenance notes."""
        notes_templates = {
            'visual_inspection': [
                "Visual inspection completed. No abnormalities observed.",
                "Inspection completed. Minor dust accumulation, cleaned.",
                "All batteries visually normal. Connection terminals clean."
            ],
            'voltage_measurement': [
                f"Voltage measurement completed for {asset_code or 'all batteries'}. All within normal range.",
                "Battery voltages measured and recorded. No significant imbalance detected.",
                "Voltage check OK. Max deviation: 0.05V."
            ],
            'thermal_survey': [
                "IR thermal scan completed. All batteries within normal temperature range.",
                "Thermal survey done. Minor hot spot on Battery #12 (within acceptable range).",
                "Infrared scan completed. Temperature distribution normal."
            ],
            'torque_check': [
                "Torque check completed. All connections within spec.",
                "Connection terminals checked and re-torqued as needed.",
                "Torque verification done. 2 connections adjusted."
            ],
            'capacity_test': [
                f"Capacity test completed for {asset_code or 'string'}. Result: PASS (96% of rated).",
                f"Discharge test done. Capacity measured: 115Ah (PASS).",
                f"Capacity test result: MARGINAL (88% of rated). Schedule for retest in 3 months."
            ],
            'impedance_test': [
                f"Impedance test completed for {asset_code or 'string'}. All batteries within normal range.",
                "Conductance measurement done. No batteries flagged.",
                "Impedance scan complete. Average: 3.2mΩ (GOOD)."
            ]
        }

        templates = notes_templates.get(event_type, ["Maintenance completed."])
        return np.random.choice(templates)

    def generate_capacity_test_data(
        self,
        maintenance_events: pd.DataFrame,
        strings: pd.DataFrame,
        batteries: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate capacity test raw and calculated data.

        Args:
            maintenance_events: Maintenance events DataFrame
            strings: Strings DataFrame
            batteries: Batteries DataFrame

        Returns:
            Tuple of (capacity_test_raw, capacity_test_calc)
        """
        capacity_tests_raw = []
        capacity_tests_calc = []

        # Filter capacity test events
        capacity_events = maintenance_events[
            maintenance_events['event_type'] == 'capacity_test'
        ]

        for _, event in capacity_events.iterrows():
            if event['string_id'] is None:
                continue

            test_id = uuid.uuid4()

            # String info
            string_info = strings[strings['string_id'] == event['string_id']].iloc[0]
            num_batteries = string_info['batteries_count']

            # Test parameters (typical for VRLA)
            discharge_rate = 10.0  # 10A discharge (0.1C for 100Ah battery)
            cutoff_voltage = 1.75 * num_batteries  # 1.75V per cell minimum

            # Simulate test duration based on battery health
            # Healthy batteries: ~10 hours, degraded: less
            duration_minutes = np.random.uniform(480, 600)  # 8-10 hours

            # Calculate capacity
            measured_capacity = (discharge_rate * duration_minutes) / 60.0

            # Ambient temp during test
            ambient_temp = np.random.uniform(22, 28)

            capacity_tests_raw.append({
                'test_id': test_id,
                'string_id': event['string_id'],
                'maintenance_event_id': event['event_id'],
                'test_date': event['completed_date'],
                'test_type': 'full_discharge',
                'discharge_rate_a': discharge_rate,
                'discharge_duration_min': round(duration_minutes, 1),
                'cutoff_voltage_v': cutoff_voltage,
                'ambient_temp_c': round(ambient_temp, 1),
                'raw_data_url': f"s3://capacity-tests/{test_id}.csv",
                'notes': 'Full discharge capacity test'
            })

            # Calculated results
            rated_capacity = 120.0  # Assuming HX12-120 (120Ah rated)
            capacity_pct = (measured_capacity / rated_capacity) * 100

            if capacity_pct >= 90:
                pass_fail = 'pass'
            elif capacity_pct >= 80:
                pass_fail = 'marginal'
            else:
                pass_fail = 'fail'

            capacity_tests_calc.append({
                'test_id': test_id,
                'measured_capacity_ah': round(measured_capacity, 2),
                'capacity_pct_of_rated': round(capacity_pct, 2),
                'pass_fail': pass_fail
            })

        raw_df = pd.DataFrame(capacity_tests_raw)
        calc_df = pd.DataFrame(capacity_tests_calc)

        print(f"  Generated {len(raw_df):,} capacity test records")

        return raw_df, calc_df

    def generate_impedance_measurements(
        self,
        maintenance_events: pd.DataFrame,
        batteries: pd.DataFrame,
        battery_degradation_states: Dict
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate impedance measurement raw and calculated data.

        Args:
            maintenance_events: Maintenance events DataFrame
            batteries: Batteries DataFrame
            battery_degradation_states: Battery states

        Returns:
            Tuple of (impedance_raw, impedance_calc)
        """
        impedance_raw = []
        impedance_calc = []

        # Filter impedance test events
        impedance_events = maintenance_events[
            maintenance_events['event_type'] == 'impedance_test'
        ]

        for _, event in impedance_events.iterrows():
            if event['string_id'] is None:
                continue

            # Get all batteries in this string
            string_batteries = batteries[batteries['string_id'] == event['string_id']]

            for _, battery in string_batteries.iterrows():
                measurement_id = uuid.uuid4()

                # Get current battery state
                battery_id_str = str(battery['battery_id'])
                if battery_id_str in battery_degradation_states:
                    state = battery_degradation_states[battery_id_str]
                    resistance = state['resistance_mohm']
                else:
                    resistance = battery['initial_resistance_mohm']

                # Add measurement noise
                resistance_measured = resistance * np.random.normal(1.0, 0.05)
                conductance = 1.0 / (resistance_measured * 0.001)

                # Temperature during measurement
                temp_c = np.random.uniform(23, 28)

                impedance_raw.append({
                    'measurement_id': measurement_id,
                    'battery_id': battery['battery_id'],
                    'maintenance_event_id': event['event_id'],
                    'measured_at': event['completed_date'],
                    'resistance_mohm': round(resistance_measured, 3),
                    'conductance_s': round(conductance, 5),
                    'temperature_c': round(temp_c, 1),
                    'instrument_model': np.random.choice(['Hioki 3554', 'Megger BITE5', 'Amprobe BAT-250'])
                })

                # Calculated (temperature-normalized)
                # Arrhenius correction to 25°C reference
                temp_ref = 25.0
                temp_correction_factor = np.exp(0.03 * (temp_c - temp_ref))
                temp_corrected_resistance = resistance_measured / temp_correction_factor

                # Baseline percentage
                initial_resistance = battery['initial_resistance_mohm']
                baseline_pct = (temp_corrected_resistance / initial_resistance) * 100

                impedance_calc.append({
                    'measurement_id': measurement_id,
                    'temp_corrected_resistance_mohm': round(temp_corrected_resistance, 3),
                    'baseline_pct': round(baseline_pct, 2)
                })

        raw_df = pd.DataFrame(impedance_raw)
        calc_df = pd.DataFrame(impedance_calc)

        print(f"  Generated {len(raw_df):,} impedance measurement records")

        return raw_df, calc_df
