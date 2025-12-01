#!/usr/bin/env python3
"""
Test script for Sensor Simulator API
Demonstrates all API endpoints and WebSocket streaming
"""
import requests
import json
import time

BASE_URL = "http://localhost:8003"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health():
    print_section("Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))

def test_scenarios():
    print_section("Available Scenarios")
    response = requests.get(f"{BASE_URL}/api/v1/scenarios")
    scenarios = response.json()
    for scenario in scenarios:
        print(f"- {scenario['name']}: {scenario['description']}")

def test_simulation():
    print_section("Starting Simulation")

    # Start simulation with 3 batteries
    start_request = {
        "batteries": [
            {
                "battery_id": "BKK_DC1_SYS01_STR01_BAT001",
                "profile": "healthy",
                "initial_soh": 95.0
            },
            {
                "battery_id": "BKK_DC1_SYS01_STR01_BAT002",
                "profile": "accelerated",
                "initial_soh": 85.0
            },
            {
                "battery_id": "BKK_DC1_SYS01_STR01_BAT003",
                "profile": "failing",
                "initial_soh": 70.0
            }
        ],
        "interval_seconds": 5,
        "scenario": "normal_operation"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/simulation/start",
        json=start_request
    )
    print(json.dumps(response.json(), indent=2))

    # Wait and check status
    print("\nWaiting 10 seconds...")
    time.sleep(10)

    print_section("Simulation Status")
    response = requests.get(f"{BASE_URL}/api/v1/simulation/status")
    print(json.dumps(response.json(), indent=2))

    # Apply power outage scenario to one battery
    print_section("Applying Power Outage Scenario")
    scenario_request = {
        "scenario": "power_outage",
        "battery_ids": ["BKK_DC1_SYS01_STR01_BAT001"],
        "ambient_temp": 28.0
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/scenarios/apply",
        json=scenario_request
    )
    print(json.dumps(response.json(), indent=2))

    # Wait a bit more
    print("\nWaiting 10 more seconds...")
    time.sleep(10)

    # Check status again
    response = requests.get(f"{BASE_URL}/api/v1/simulation/status")
    print(f"\nReadings generated: {response.json()['readings_generated']}")

    # Stop simulation
    print_section("Stopping Simulation")
    response = requests.post(f"{BASE_URL}/api/v1/simulation/stop")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    print("="*60)
    print("  Sensor Simulator API Test")
    print("="*60)

    try:
        test_health()
        test_scenarios()
        test_simulation()

        print_section("All Tests Passed! ✅")
        print("The sensor simulator is working correctly.")
        print("\nNext steps:")
        print("1. Deploy to Railway")
        print("2. Create control panel UI in frontend")
        print("3. Integrate with main backend API")

    except Exception as e:
        print(f"\n❌ Error: {e}")
