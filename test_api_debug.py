#!/usr/bin/env python3
"""Test script to debug the workflow symbol creation API"""
import json
import requests

API_URL = "http://localhost:8000/api/workflow-symbols/"

test_payload = {
    "symbol": "DEBG",
    "name": "Debug Test Stock",
    "priority": 0,
    "enabled": True,
    "conid": 999888,
    "workflows": [{
        "dag_id": "finagent_trading_signal_workflow",
        "is_active": True,
        "timezone": "America/New_York",
        "session_start": "09:30",
        "session_end": "16:00",
        "allow_weekend": False,
        "schedule_interval": "0 9 * * *",
        "config": None
    }]
}

print("Testing POST to", API_URL)
print("Payload:", json.dumps(test_payload, indent=2))
print("\n" + "="*50)

try:
    response = requests.post(API_URL, json=test_payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"\n❌ Request failed: {e}")
