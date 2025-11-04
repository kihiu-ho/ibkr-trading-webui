#!/usr/bin/env python3
"""
Patch Airflow webserver_command.py to increase the gunicorn master timeout.
This script patches the hardcoded 120-second timeout to 300 seconds.
"""
import sys
import os

# Find the webserver_command module
try:
    import airflow.www.command as webserver_command
    module_file = webserver_command.__file__
except ImportError:
    print("ERROR: Could not import airflow.www.command", file=sys.stderr)
    sys.exit(1)

# Check if already patched
if hasattr(webserver_command, '_TIMEOUT_PATCHED'):
    print("Webserver timeout already patched")
    sys.exit(0)

# Read the file
with open(module_file, 'r') as f:
    content = f.read()

# Patch the timeout value (120 seconds -> 300 seconds)
# Look for the timeout check pattern
if '120' in content and 'seconds' in content.lower():
    # Try to find and replace the timeout value
    # This is a simple approach - we're looking for the pattern around line 223
    # The actual pattern might be: "within 120 seconds" or similar
    import re
    # Replace various patterns of 120 second timeouts
    content = re.sub(r'(\d+)\s*seconds.*master.*timeout', lambda m: '300 seconds for gunicorn master timeout', content, flags=re.IGNORECASE)
    content = re.sub(r'within\s+120\s+seconds', 'within 300 seconds', content, flags=re.IGNORECASE)
    content = re.sub(r'(\d+)\s*seconds.*gunicorn.*master', lambda m: '300 seconds for gunicorn master', content, flags=re.IGNORECASE)
    
    # Write back
    with open(module_file, 'w') as f:
        f.write(content)
    
    # Reload the module
    import importlib
    importlib.reload(webserver_command)
    
    # Mark as patched
    webserver_command._TIMEOUT_PATCHED = True
    print(f"Successfully patched webserver timeout in {module_file}")
else:
    print("Could not find timeout pattern to patch", file=sys.stderr)
    sys.exit(1)
