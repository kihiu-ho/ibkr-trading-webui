#!/usr/bin/env python3
"""Direct backend test to see actual error"""
import sys
import traceback
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import time
from backend.api.workflow_symbols import SymbolWorkflowConfig

# Test the time parsing
print("Testing SymbolWorkflowConfig with time strings...")
print("="*60)

test_data = {
    "dag_id": "finagent_trading_signal_workflow",
    "is_active": True,
    "timezone": "America/New_York",
    "session_start": "09:30",
    "session_end": "16:00",
    "allow_weekend": False,
    "schedule_interval": "0 9 * * *",
    "config": None
}

try:
    config = SymbolWorkflowConfig(**test_data)
    print("✅ SymbolWorkflowConfig created successfully!")
    print(f"   dag_id: {config.dag_id}")
    print(f"   session_start: {config.session_start} (type: {type(config.session_start)})")
    print(f"   session_end: {config.session_end} (type: {type(config.session_end)})")
except Exception as e:
    print(f"❌ Error creating SymbolWorkflowConfig:")
    print(f"   {e}")
    traceback.print_exc()
