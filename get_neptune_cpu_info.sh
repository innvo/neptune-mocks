#!/bin/bash

# Get Neptune CPU and System Information
# This script retrieves information about CPU usage and system resources

NEPTUNE_ENDPOINT="localhost:8182"

echo "Getting Neptune CPU and System Information..."
echo "Endpoint: $NEPTUNE_ENDPOINT"
echo "=" * 80

# Get system status and CPU information
echo "1. System Status (includes CPU info):"
echo "-" * 50
curl -k -X GET \
  "https://$NEPTUNE_ENDPOINT/status"

echo ""
echo ""
echo "2. Detailed System Information:"
echo "-" * 50
curl -k -X GET \
  "https://$NEPTUNE_ENDPOINT/system"

echo ""
echo ""
echo "3. Cluster Information:"
echo "-" * 50
curl -k -X GET \
  "https://$NEPTUNE_ENDPOINT/cluster"

echo ""
echo ""
echo "4. Metrics Information:"
echo "-" * 50
curl -k -X GET \
  "https://$NEPTUNE_ENDPOINT/metrics"

echo ""
echo ""
echo "5. Instance Information:"
echo "-" * 50
curl -k -X GET \
  "https://$NEPTUNE_ENDPOINT/instance"

echo ""
echo ""
echo "Working endpoints for CPU and system information:"
echo "- /status (main endpoint with system info)"
echo "- /system (detailed system information)"
echo "- /cluster (cluster configuration)"
echo "- /metrics (performance metrics)"
echo "- /instance (instance details)"
echo ""
echo "Note: Some endpoints may return 404 if not available in your Neptune version." 