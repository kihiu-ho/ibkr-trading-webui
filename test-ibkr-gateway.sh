#!/bin/bash
# Test IBKR Gateway Service

echo "🧪 Testing IBKR Gateway Service..."
echo ""

# Check container status
echo "1. Container Status:"
docker compose ps ibkr-gateway
echo ""

# Check if gateway is listening
echo "2. Port Connectivity:"
if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:5055/v1/api/tickle | grep -q "401\|403"; then
    echo "✅ Gateway is responding (authentication required)"
else
    echo "⏳ Gateway may still be initializing..."
fi
echo ""

# Check logs
echo "3. Recent Gateway Logs:"
docker logs ibkr-gateway --tail 10
echo ""

# Test from inside container
echo "4. Internal API Test:"
docker exec ibkr-gateway curl -k -s https://localhost:5055/v1/api/tickle 2>&1 | head -c 100
echo ""
echo ""

# Instructions
echo "📋 Next Steps:"
echo "   1. Open https://localhost:5055 in your browser"
echo "   2. Accept the security warning (self-signed certificate)"
echo "   3. Log in with your IBKR credentials"
echo "   4. Gateway will be authenticated and ready to use"
echo ""
echo "✅ IBKR Gateway Test Complete!"

