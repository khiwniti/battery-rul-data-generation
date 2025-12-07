"""
Master Data Generators for Battery RUL Prediction System

Generates reference tables for:
- Locations (9 data centers across Thailand)
- Battery models (VRLA specifications)
- Battery systems (UPS and Rectifier)
- Strings (series-connected batteries)
- Batteries (individual jars)
- Environmental sensors
- Users
- ML models
"""

import uuid
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np


class MasterDataGenerator:
    """Generate master reference data for Thai battery fleet."""

    # Real Thai cities and regions
    THAI_LOCATIONS = [
        {
            'code': 'DC-CNX-01',
            'name': 'Chiangmai Data Center',
            'region': 'northern',
            'city': 'Chiangmai',
            'lat': 18.7883,
            'lon': 98.9853,
            'commissioned': '2018-03-15'
        },
        {
            'code': 'DC-KKN-01',
            'name': 'Khon Kaen Data Center',
            'region': 'northeastern',
            'city': 'Khon Kaen',
            'lat': 16.4322,
            'lon': 102.8236,
            'commissioned': '2019-07-01'
        },
        {
            'code': 'DC-NTB-01',
            'name': 'Nonthaburi Data Center',
            'region': 'central',
            'city': 'Nonthaburi',
            'lat': 13.8598,
            'lon': 100.5254,
            'commissioned': '2017-01-20'
        },
        {
            'code': 'DC-BKK-01',
            'name': 'Bangrak Data Center',
            'region': 'central',
            'city': 'Bangkok',
            'lat': 13.7248,
            'lon': 100.5310,
            'commissioned': '2016-11-10'
        },
        {
            'code': 'DC-BKK-02',
            'name': 'Phrakhanong Data Center',
            'region': 'central',
            'city': 'Bangkok',
            'lat': 13.7051,
            'lon': 100.6040,
            'commissioned': '2020-02-15'
        },
        {
            'code': 'DC-SRC-01',
            'name': 'Sriracha Data Center',
            'region': 'eastern',
            'city': 'Sriracha',
            'lat': 13.1664,
            'lon': 100.9308,
            'commissioned': '2019-05-20'
        },
        {
            'code': 'DC-URT-01',
            'name': 'Surat Thani Data Center',
            'region': 'southern',
            'city': 'Surat Thani',
            'lat': 9.1355,
            'lon': 99.3331,
            'commissioned': '2020-08-01'
        },
        {
            'code': 'DC-PKT-01',
            'name': 'Phuket Data Center',
            'region': 'southern',
            'city': 'Phuket',
            'lat': 7.8804,
            'lon': 98.3923,
            'commissioned': '2018-12-01'
        },
        {
            'code': 'DC-HDY-01',
            'name': 'Hat Yai Data Center',
            'region': 'southern',
            'city': 'Hat Yai',
            'lat': 7.0061,
            'lon': 100.4667,
            'commissioned': '2021-03-15'
        }
    ]

    # Standard battery models used in Thai facilities
    BATTERY_MODELS = [
        {
            'model_name': 'HX12-120',
            'manufacturer': 'CSB Battery',
            'chemistry': 'VRLA',
            'nominal_voltage': 12.0,
            'capacity_ah': 120.0,
            'float_voltage_min': 13.50,
            'float_voltage_max': 13.80,
            'boost_voltage_min': 14.40,
            'boost_voltage_max': 14.70,
            'max_charge_current': 36.0,
            'temp_warning': 45.0,
            'temp_critical': 50.0,
            'expected_life_years': 10.0
        },
        {
            'model_name': 'GPL12-100',
            'manufacturer': 'GS Battery',
            'chemistry': 'VRLA',
            'nominal_voltage': 12.0,
            'capacity_ah': 100.0,
            'float_voltage_min': 13.50,
            'float_voltage_max': 13.80,
            'boost_voltage_min': 14.40,
            'boost_voltage_max': 14.70,
            'max_charge_current': 30.0,
            'temp_warning': 45.0,
            'temp_critical': 50.0,
            'expected_life_years': 8.0
        }
    ]

    def __init__(self, seed: int = 42):
        """Initialize master data generator with random seed."""
        self.seed = seed
        np.random.seed(seed)
        self.location_ids = {}
        self.system_ids = {}
        self.string_ids = {}
        self.battery_ids = {}
        self.model_ids = {}

    def generate_locations(self) -> pd.DataFrame:
        """Generate location master data."""
        locations = []

        for loc in self.THAI_LOCATIONS:
            location_id = uuid.uuid4()
            self.location_ids[loc['code']] = location_id

            locations.append({
                'location_id': location_id,
                'location_code': loc['code'],
                'location_name': loc['name'],
                'region': loc['region'],
                'city': loc['city'],
                'latitude': loc['lat'],
                'longitude': loc['lon'],
                'timezone': 'Asia/Bangkok',
                'commissioned_date': pd.to_datetime(loc['commissioned']),
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })

        return pd.DataFrame(locations)

    def generate_battery_models(self) -> pd.DataFrame:
        """Generate battery model specifications."""
        models = []

        for model in self.BATTERY_MODELS:
            model_id = uuid.uuid4()
            self.model_ids[model['model_name']] = model_id

            models.append({
                'model_id': model_id,
                'model_name': model['model_name'],
                'manufacturer': model['manufacturer'],
                'chemistry': model['chemistry'],
                'nominal_voltage_v': model['nominal_voltage'],
                'capacity_ah': model['capacity_ah'],
                'float_voltage_min_v': model['float_voltage_min'],
                'float_voltage_max_v': model['float_voltage_max'],
                'boost_voltage_min_v': model['boost_voltage_min'],
                'boost_voltage_max_v': model['boost_voltage_max'],
                'max_charge_current_a': model['max_charge_current'],
                'temp_warning_c': model['temp_warning'],
                'temp_critical_c': model['temp_critical'],
                'expected_life_years': model['expected_life_years'],
                'datasheet_url': f'https://example.com/datasheets/{model["model_name"]}.pdf'
            })

        return pd.DataFrame(models)

    def generate_battery_systems(self, locations_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate battery systems (UPS and Rectifier) for each location.

        Each site typically has:
        - 1 Rectifier bank (for DC systems)
        - 1-2 UPS systems (for AC systems)
        """
        systems = []

        for _, loc in locations_df.iterrows():
            location_code = loc['location_code']
            location_id = loc['location_id']
            commissioned = loc['commissioned_date']

            # Rectifier system (1 per site)
            system_id = uuid.uuid4()
            system_code = f"{location_code}-REC-01"
            self.system_ids[system_code] = system_id

            systems.append({
                'system_id': system_id,
                'location_id': location_id,
                'system_code': system_code,
                'system_type': 'RECTIFIER',
                'system_name': f'{loc["city"]} Rectifier Bank',
                'manufacturer': np.random.choice(['Emerson', 'Vertiv', 'Huawei']),
                'model': 'R48-3000',
                'rated_power_kva': 150.0,
                'installed_date': commissioned,
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })

            # UPS systems (1-2 per site, larger sites have 2)
            num_ups = 2 if loc['region'] == 'central' else 1

            for ups_idx in range(1, num_ups + 1):
                system_id = uuid.uuid4()
                system_code = f"{location_code}-UPS-{ups_idx:02d}"
                self.system_ids[system_code] = system_id

                systems.append({
                    'system_id': system_id,
                    'location_id': location_id,
                    'system_code': system_code,
                    'system_type': 'UPS',
                    'system_name': f'{loc["city"]} UPS-{ups_idx}',
                    'manufacturer': np.random.choice(['APC', 'Eaton', 'Schneider Electric']),
                    'model': 'Galaxy 5500',
                    'rated_power_kva': 200.0,
                    'installed_date': commissioned,
                    'is_active': True,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })

        return pd.DataFrame(systems)

    def generate_strings(self, systems_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate battery strings for each system.

        Typical configuration:
        - Rectifier: 3 strings
        - UPS: 6 strings
        - Each string: 24 batteries in series
        """
        strings = []

        for _, sys in systems_df.iterrows():
            system_code = sys['system_code']
            system_id = sys['system_id']
            system_type = sys['system_type']

            # Number of strings based on system type
            num_strings = 3 if system_type == 'RECTIFIER' else 6

            for string_idx in range(1, num_strings + 1):
                string_id = uuid.uuid4()
                string_code = f"{system_code}-S{string_idx}"
                self.string_ids[string_code] = string_id

                strings.append({
                    'string_id': string_id,
                    'system_id': system_id,
                    'string_code': string_code,
                    'string_position': string_idx,
                    'batteries_count': 24,
                    'nominal_voltage_v': 288.0,  # 24 * 12V
                    'installed_date': sys['installed_date'],
                    'last_capacity_test_date': None,
                    'is_active': True,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })

        return pd.DataFrame(strings)

    def generate_batteries(
        self,
        strings_df: pd.DataFrame,
        models_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate individual battery jars.

        Each battery has:
        - Unique serial number
        - Manufacturing date (3-6 months before installation)
        - Initial capacity and resistance measurements
        """
        batteries = []

        # Use primarily HX12-120 model (80%), rest GPL12-100
        primary_model = models_df[models_df['model_name'] == 'HX12-120'].iloc[0]
        secondary_model = models_df[models_df['model_name'] == 'GPL12-100'].iloc[0]

        for _, string in strings_df.iterrows():
            string_code = string['string_code']
            string_id = string['string_id']
            installed_date = string['installed_date']

            for pos in range(1, 25):  # 24 batteries per string
                battery_id = uuid.uuid4()
                battery_code = f"{string_code}-J{pos:02d}"
                self.battery_ids[battery_code] = battery_id

                # Choose model (80% primary, 20% secondary)
                model = primary_model if np.random.random() < 0.8 else secondary_model

                # Manufacturing date (3-6 months before installation)
                manufacture_offset = np.random.randint(90, 180)
                manufacture_date = installed_date - timedelta(days=manufacture_offset)

                # Warranty (typically 2 years for VRLA)
                warranty_expiry = installed_date + timedelta(days=730)

                # PRODUCTION-GRADE: Manufacturing variation based on real battery specs
                # Capacity tolerance: ±2.5% (typical for VRLA, per IEC 61056 standards)
                capacity_tolerance = 0.025
                initial_capacity = model['capacity_ah'] * np.random.normal(1.0, capacity_tolerance)

                # Resistance varies with capacity (larger batteries have lower resistance)
                # Typical: 120Ah battery = 3.0-4.0 mΩ, 65Ah battery = 5.0-6.0 mΩ
                # Using empirical relationship: R ≈ 360 / C (mΩ-Ah)
                nominal_resistance = 360.0 / model['capacity_ah']  # Typical for VRLA
                # Manufacturing tolerance: ±10% for resistance (wider than capacity)
                resistance_tolerance = 0.10
                initial_resistance = nominal_resistance * np.random.normal(1.0, resistance_tolerance)

                batteries.append({
                    'battery_id': battery_id,
                    'string_id': string_id,
                    'model_id': model['model_id'],
                    'battery_code': battery_code,
                    'serial_number': f"SN{manufacture_date.year}{np.random.randint(100000, 999999)}",
                    'position_in_string': pos,
                    'manufacture_date': manufacture_date,
                    'installed_date': installed_date,
                    'warranty_expiry_date': warranty_expiry,
                    'initial_capacity_ah': round(initial_capacity, 2),
                    'initial_resistance_mohm': round(initial_resistance, 3),
                    'status': 'active',
                    'replacement_of': None,
                    'replaced_date': None,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })

        return pd.DataFrame(batteries)

    def generate_environmental_sensors(self, locations_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate environmental sensors for each location.

        Typical setup: 2-4 sensors per data center
        """
        sensors = []

        zones = ['Battery Room 1', 'Battery Room 2', 'UPS Room', 'Rectifier Room']

        for _, loc in locations_df.iterrows():
            location_code = loc['location_code']
            location_id = loc['location_id']

            # 2-4 sensors depending on site size
            num_sensors = 4 if loc['region'] == 'central' else 2

            for sensor_idx in range(1, num_sensors + 1):
                sensor_id = uuid.uuid4()

                sensors.append({
                    'sensor_id': sensor_id,
                    'location_id': location_id,
                    'sensor_code': f"{location_code}-ENV{sensor_idx:02d}",
                    'sensor_type': 'combined',  # Temperature + Humidity
                    'zone': zones[sensor_idx - 1] if sensor_idx <= len(zones) else f'Zone {sensor_idx}',
                    'is_active': True
                })

        return pd.DataFrame(sensors)

    def generate_users(self) -> pd.DataFrame:
        """Generate system users (engineers, operators, admins)."""
        users = []

        # Sample users
        user_data = [
            ('admin@datacenter.co.th', 'Somchai Srisawat', 'admin'),
            ('engineer1@datacenter.co.th', 'Nattapong Wongsiri', 'engineer'),
            ('engineer2@datacenter.co.th', 'Siriporn Thongchai', 'engineer'),
            ('operator1@datacenter.co.th', 'Wanchai Prasert', 'operator'),
            ('operator2@datacenter.co.th', 'Supaporn Yamyong', 'operator'),
            ('viewer@datacenter.co.th', 'Anan Chaiyaporn', 'viewer')
        ]

        for email, name, role in user_data:
            users.append({
                'user_id': uuid.uuid4(),
                'email': email,
                'name': name,
                'role': role,
                'location_ids': list(self.location_ids.values()),  # All locations
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })

        return pd.DataFrame(users)

    def generate_ml_models(self) -> pd.DataFrame:
        """Generate ML model registry entries."""
        models = []

        model_configs = [
            {
                'name': 'CatBoost RUL Regressor v1.0',
                'type': 'catboost_rul',
                'version': '1.0.0',
                'status': 'production'
            },
            {
                'name': 'Isolation Forest Anomaly Detector v1.0',
                'type': 'anomaly_iforest',
                'version': '1.0.0',
                'status': 'production'
            },
            {
                'name': 'CatBoost RUL Regressor v1.1',
                'type': 'catboost_rul',
                'version': '1.1.0',
                'status': 'staging'
            }
        ]

        for config in model_configs:
            trained_at = datetime.now() - timedelta(days=np.random.randint(30, 180))

            models.append({
                'model_id': uuid.uuid4(),
                'model_name': config['name'],
                'model_type': config['type'],
                'version': config['version'],
                'status': config['status'],
                'trained_at': trained_at,
                'promoted_at': trained_at + timedelta(days=7) if config['status'] == 'production' else None,
                'retired_at': None,
                'artifact_url': f's3://ml-models/{config["type"]}/{config["version"]}/model.cbm',
                'hyperparameters_json': {
                    'iterations': 1000,
                    'learning_rate': 0.03,
                    'depth': 6
                },
                'metrics_json': {
                    'mae': 12.5,
                    'rmse': 18.3,
                    'r2': 0.87
                },
                'feature_list': [
                    'v_mean', 'v_std', 't_mean', 'r_internal_baseline_pct',
                    'discharge_cycles_count', 'ah_throughput'
                ],
                'training_data_start': trained_at - timedelta(days=365),
                'training_data_end': trained_at - timedelta(days=7),
                'created_by': None
            })

        return pd.DataFrame(models)

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """
        Generate all master data tables.

        Returns:
            Dictionary of DataFrames keyed by table name
        """
        print("Generating master data...")

        data = {}

        print("  - Locations (9 sites)...")
        data['location'] = self.generate_locations()

        print("  - Battery models (2 models)...")
        data['battery_model'] = self.generate_battery_models()

        print("  - Battery systems (18-27 systems)...")
        data['battery_system'] = self.generate_battery_systems(data['location'])

        print("  - Strings (81 strings)...")
        data['string'] = self.generate_strings(data['battery_system'])

        print("  - Batteries (1,944 jars)...")
        data['battery'] = self.generate_batteries(data['string'], data['battery_model'])

        print("  - Environmental sensors...")
        data['environmental_sensor'] = self.generate_environmental_sensors(data['location'])

        print("  - Users...")
        data['user'] = self.generate_users()

        print("  - ML models...")
        data['ml_model'] = self.generate_ml_models()

        print(f"Master data generation complete:")
        for table, df in data.items():
            print(f"    {table}: {len(df)} records")

        return data
