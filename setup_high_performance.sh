#!/bin/bash
# High-Performance Neptune Load Setup Script
#
# This script sets up environment variables for high-performance Neptune bulk loading
# with 15 concurrent files. Run this script before executing the bulk loader.
#
# Usage:
#     source setup_high_performance.sh
#     python src/generate/gremlin/bulk_load_nodes_edges.py

echo "🚀 Setting up High-Performance Neptune Environment for 15 Concurrent Files"
echo "=================================================================="

# Core Neptune settings
export NEPTUNE_CONCURRENT_LIMIT=15
export NEPTUNE_ULTRA_MODE=true
export NEPTUNE_PARALLELISM=OVERSUBSCRIBE
export NEPTUNE_FAIL_ON_ERROR=false
export NEPTUNE_QUEUE_REQUEST=false

# Performance tuning for maximum speed
export NEPTUNE_QUEUE_WAIT_TIME=1
export NEPTUNE_MAX_RETRY_ATTEMPTS=1
export NEPTUNE_BACKOFF_MULTIPLIER=1.1
export NEPTUNE_INITIAL_BACKOFF=2
export NEPTUNE_MAX_BACKOFF=10
export NEPTUNE_HEALTH_CHECK_INTERVAL=5
export NEPTUNE_TIMEOUT=10800
export NEPTUNE_CONNECT_TIMEOUT=10

# Optional debugging (set to true if you need detailed logs)
export NEPTUNE_DEBUG=false

echo "✅ High-Performance Environment Variables Set:"
echo "   • Concurrent Limit: 15 files"
echo "   • Mode: Ultra Performance"
echo "   • Parallelism: OVERSUBSCRIBE"
echo "   • Queue Wait Time: 1 second"
echo "   • Retry Attempts: 1"
echo "   • Timeout: 3 hours"
echo "   • Health Check: Every 5 seconds"
echo ""
echo "📋 Next Steps:"
echo "   1. Ensure NEPTUNE_IAM_ROLE_ARN is set"
echo "   2. Run: python src/generate/gremlin/bulk_load_nodes_edges.py"
echo ""
echo "⚠️  Warning: This configuration is optimized for maximum speed."
echo "   It may overwhelm smaller Neptune clusters. Monitor your cluster's performance."
echo ""
echo "🔧 To revert to default settings, run: unset NEPTUNE_ULTRA_MODE NEPTUNE_CONCURRENT_LIMIT" 