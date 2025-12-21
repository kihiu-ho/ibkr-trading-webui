#!/usr/bin/env python3
"""Test script with detailed error logging"""
import json
import requests
import traceback

API_URL = "http://localhost:8000/api/workflow-symbols/"

test_payload = {
    "symbol": "TESTERR",
    "name": "Test Error Stock",
    "priority": 0,
    "enabled": True,
    "conid": 123456,
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
print("="*60)

try:
    response = requests.post(API_URL, json=test_payload, timeout=10)
    print(f"\n✓ Status Code: {response.status_code}")
    print(f"\nResponse Body:")
    try:
        resp_json = response.json()
        print(json.dumps(resp_json, indent=2))
    except:
        print(response.text)
        
    if response.status_code == 500:
        print("\n❌ 500 Internal Server Error - Check backend logs for details")
    elif response.status_code >= 400:
        print(f"\n❌ Error {response.status_code}")
    else:
        print("\n✅ Success!")
        
except Exception as e:
    print(f"\n❌ Request failed: {e}")
    traceback.print_exc()
