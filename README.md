# Battery RUL Prediction - Data Generation

Synthetic data generation system for Battery RUL (Remaining Useful Life) prediction in Thai data centers.

## Quick Start on Kaggle

1. Install dependencies:
```python
!pip install numpy pandas scipy pytz faker tqdm matplotlib seaborn
```

2. Clone and run:
```python
!git clone https://github.com/YOUR_USERNAME/battery-rul-data-generation.git
%cd battery-rul-data-generation
!python generate_full_dataset.py --days 730 --batteries-per-location 24 --sampling-seconds 60
```

## Local Usage

```bash
# Quick test (2 days, 24 batteries)
python generate_battery_data.py --duration-days 2 --limit-batteries 24 --sampling-seconds 300

# Full dataset (2 years, 216 batteries)
python generate_full_dataset.py --days 730 --batteries-per-location 24 --sampling-seconds 60
```

## Features
- Physics-based battery degradation
- Thai environmental conditions (3 seasons, 5 regions)
- Power outages and HVAC failures
- 227+ million records for full 2-year dataset

See documentation for details.
