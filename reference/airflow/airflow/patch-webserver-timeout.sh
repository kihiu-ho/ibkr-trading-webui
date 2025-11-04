#!/bin/bash
# Patch Airflow's webserver timeout from 120 to 300 seconds
python3 << 'EOF'
import sys, os, re
try:
    import airflow.www.command as ws_cmd
    module_file = ws_cmd.__file__
    if module_file.endswith('.pyc'):
        module_file = module_file[:-1]
    with open(module_file, 'r') as f:
        content = f.read()
    original = content
    # Replace 120 seconds with 300 seconds
    content = re.sub(r'120\s*seconds', '300 seconds', content)
    content = re.sub(r'timeout\s*=\s*120', 'timeout = 300', content)
    if content != original:
        with open(module_file, 'w') as f:
            f.write(content)
        # Invalidate Python cache
        if os.path.exists(module_file + 'c'):
            os.remove(module_file + 'c')
        print(f"Patched webserver timeout to 300 seconds in {module_file}")
    else:
        print("Could not find timeout pattern to patch")
except Exception as e:
    print(f"Warning: Could not patch timeout: {e}", file=sys.stderr)
EOF
