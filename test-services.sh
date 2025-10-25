#!/bin/bash
# Quick service test script

echo "🧪 Testing IBKR Trading WebUI Services..."
echo ""

# Test backend health
echo "1. Backend Health Check:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Test database
echo "2. Database Connection:"
docker exec ibkr-postgres psql -U postgres -d ibkr_trading -c 'SELECT count(*) as tables FROM information_schema.tables WHERE table_schema = '\''public'\'';' 2>&1 | grep -E "tables|---"
echo ""

# Test Redis
echo "3. Redis Connection:"
docker exec ibkr-redis redis-cli ping
echo ""

# Test MinIO
echo "4. MinIO Health:"
docker exec ibkr-minio curl -s http://localhost:9000/minio/health/live && echo "OK" || echo "Not Ready"
echo ""

# Check service status
echo "5. All Services Status:"
docker compose ps --format "table {{.Service}}\t{{.State}}"
echo ""

echo "✅ Test Complete!"
