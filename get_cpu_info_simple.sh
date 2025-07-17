#!/bin/bash

# Simple curl command to get Neptune CPU information
# This is the most common endpoint for system status

echo "Getting Neptune CPU and System Status..."
echo "=" * 50

# The main status endpoint that includes CPU information
curl -k -X GET \
  "https://localhost:8182/status"

echo ""
echo ""
echo "This endpoint typically includes:"
echo "- CPU usage information"
echo "- Memory usage"
echo "- System status"
echo "- Cluster health"
echo "- Available resources" 