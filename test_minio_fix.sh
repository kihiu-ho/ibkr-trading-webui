#!/bin/bash
# Simple test for MinIO URL fix

set -e

echo "=================================="
echo "Testing MinIO URL Fix"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "1. Testing chart generation..."
response=$(curl -s -X POST "http://localhost:8000/api/charts/generate" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","indicator_ids":[1],"period":50,"frequency":"1D"}')

echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    jpeg_url = data.get('chart_url_jpeg', '')
    html_url = data.get('chart_url_html', '')
    
    print(f'Generated Chart:')
    print(f'  ID: {data.get(\"id\")}')
    print(f'  Symbol: {data.get(\"symbol\")}')
    print(f'  JPEG URL: {jpeg_url}')
    print(f'  HTML URL: {html_url}')
    print()
    
    # Check URL format
    if 'localhost:9000' in jpeg_url:
        print('\033[0;32m✓ URLs use localhost:9000 (browser-accessible)\033[0m')
    elif 'minio:9000' in jpeg_url:
        print('\033[0;31m✗ URLs use minio:9000 (not browser-accessible)\033[0m')
        sys.exit(1)
    else:
        print('\033[0;31m✗ Unexpected URL format\033[0m')
        sys.exit(1)
    
    # Save URLs for next test
    with open('/tmp/test_urls.txt', 'w') as f:
        f.write(f'{jpeg_url}\n{html_url}')
        
except Exception as e:
    print(f'\033[0;31m✗ Error: {e}\033[0m')
    print(sys.stdin.read())
    sys.exit(1)
"

echo ""
echo "2. Testing image accessibility..."

if [ -f /tmp/test_urls.txt ]; then
    jpeg_url=$(head -n1 /tmp/test_urls.txt)
    
    echo "Testing: $jpeg_url"
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$jpeg_url")
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ Image is accessible (HTTP 200)${NC}"
    else
        echo -e "${RED}✗ Image not accessible (HTTP $http_code)${NC}"
        
        if [ "$http_code" = "403" ]; then
            echo "Run: docker exec ibkr-minio mc alias set myminio http://localhost:9000 minioadmin minioadmin"
            echo "Then: docker exec ibkr-minio mc anonymous set download myminio/trading-charts"
        fi
    fi
    
    rm /tmp/test_urls.txt
fi

echo ""
echo "3. Checking existing charts..."
curl -s "http://localhost:8000/api/charts?limit=5" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Total charts: {len(data)}')
    
    if len(data) > 0:
        localhost_count = sum(1 for c in data if 'localhost:9000' in c.get('chart_url_jpeg', ''))
        minio_count = sum(1 for c in data if 'minio:9000' in c.get('chart_url_jpeg', ''))
        
        print(f'  Using localhost:9000: {localhost_count} \033[0;32m✓\033[0m')
        print(f'  Using minio:9000: {minio_count}', end='')
        if minio_count > 0:
            print(' \033[0;31m(regenerate these)\033[0m')
        else:
            print()
except Exception as e:
    print(f'Error: {e}')
"

echo ""
echo "=================================="
echo "Test Complete!"
echo "=================================="
echo ""
echo "Next: Open http://localhost:8000/charts"
echo "  - Chart thumbnails should load"
echo "  - No ERR_NAME_NOT_RESOLVED errors"
echo ""

