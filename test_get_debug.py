#!/usr/bin/env python3
"""Test script for GET endpoint"""
import json
import requests

API_URL = "http://localhost:8000/api/workflow-symbols/"

def test_get():
    print(f"Testing GET {API_URL}...")
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            symbols = response.json()
            print(f"✅ GET successful! Found {len(symbols)} symbols.")
            for s in symbols:
                print(f" - {s['symbol']} (ID: {s['id']})")
        else:
            print(f"❌ GET failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ GET exception: {e}")

if __name__ == "__main__":
    test_get()
