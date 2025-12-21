#!/usr/bin/env python3
"""Test script for PATCH endpoint"""
import json
import requests
import sys

API_URL = "http://localhost:8000/api/workflow-symbols/"

def test_patch():
    # 1. Create a symbol first
    symbol = "TESTPATCH"
    print(f"Creating symbol {symbol}...")
    create_payload = {
        "symbol": symbol,
        "name": "Test Patch Stock",
        "priority": 10,
        "enabled": True,
        "conid": 555555,
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
    
    try:
        # cleanup first
        # We can't easily delete via API, so we just try to create. 
        # If it exists, we'll just patch it.
        resp = requests.post(API_URL, json=create_payload)
        if resp.status_code not in [200, 201]:
            print(f"Create failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Create exception: {e}")

    # 2. Patch the symbol
    print(f"Patching symbol {symbol}...")
    patch_payload = {
        "priority": 20,
        "enabled": False,
        "workflows": [{
            "dag_id": "finagent_trading_signal_workflow",
            "is_active": True,
            "timezone": "UTC",
            "session_start": "10:00",
            "session_end": "15:00",
            "allow_weekend": True,
            "schedule_interval": "0 10 * * *",
            "config": {"test": "value"}
        }]
    }
    
    response = requests.patch(f"{API_URL}{symbol}", json=patch_payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Patch successful!")
        print(f"   Priority: {data['priority']} (Expected: 20)")
        print(f"   Enabled: {data['enabled']} (Expected: False)")
        print(f"   Workflows: {len(data['workflows'])}")
        if len(data['workflows']) > 0:
            wf = data['workflows'][0]
            print(f"   Workflow DAG: {wf['dag_id']}")
            print(f"   Session: {wf['session_start']} - {wf['session_end']}")
            print(f"   Weekend: {wf['allow_weekend']}")
    else:
        print(f"❌ Patch failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_patch()
