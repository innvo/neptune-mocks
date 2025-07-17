# High-Performance Neptune Bulk Loading Setup

This guide explains how to configure Neptune bulk loading for maximum performance with 15 concurrent files.

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
# Set up high-performance environment
source setup_high_performance.sh

# Run the bulk loader
python src/generate/gremlin/bulk_load_nodes_edges.py
```

### Option 2: Manual Setup
```bash
# Core settings
export NEPTUNE_CONCURRENT_LIMIT=15
export NEPTUNE_ULTRA_MODE=true
export NEPTUNE_PARALLELISM=OVERSUBSCRIBE
export NEPTUNE_FAIL_ON_ERROR=false
export NEPTUNE_QUEUE_REQUEST=false

# Performance tuning
export NEPTUNE_QUEUE_WAIT_TIME=1
export NEPTUNE_MAX_RETRY_ATTEMPTS=1
export NEPTUNE_BACKOFF_MULTIPLIER=1.1
export NEPTUNE_INITIAL_BACKOFF=2
export NEPTUNE_MAX_BACKOFF=10
export NEPTUNE_HEALTH_CHECK_INTERVAL=5
export NEPTUNE_TIMEOUT=10800
export NEPTUNE_CONNECT_TIMEOUT=10

# Run the bulk loader
python src/generate/gremlin/bulk_load_nodes_edges.py
```

## 📋 Prerequisites

1. **Neptune Cluster**: Must support at least 15 concurrent loads
2. **IAM Role**: Set `NEPTUNE_IAM_ROLE_ARN` environment variable
3. **S3 Access**: Ensure your IAM role has read access to your S3 bucket
4. **Network**: Stable connection to your Neptune cluster

## 🔧 Configuration Details

### Core Settings
- **`NEPTUNE_CONCURRENT_LIMIT=15`**: Process up to 15 files simultaneously
- **`NEPTUNE_ULTRA_MODE=true`**: Enable ultra-performance mode
- **`NEPTUNE_PARALLELISM=OVERSUBSCRIBE`**: Maximum throughput per file
- **`NEPTUNE_FAIL_ON_ERROR=false`**: Continue processing on individual file errors
- **`NEPTUNE_QUEUE_REQUEST=false`**: Submit loads immediately

### Performance Tuning
- **`NEPTUNE_QUEUE_WAIT_TIME=1`**: Minimal wait between queue checks
- **`NEPTUNE_MAX_RETRY_ATTEMPTS=1`**: Single retry for failed loads
- **`NEPTUNE_BACKOFF_MULTIPLIER=1.1`**: Fast recovery from errors
- **`NEPTUNE_INITIAL_BACKOFF=2`**: Quick retry on failures
- **`NEPTUNE_MAX_BACKOFF=10`**: Maximum 10-second backoff
- **`NEPTUNE_HEALTH_CHECK_INTERVAL=5`**: Frequent cluster monitoring
- **`NEPTUNE_TIMEOUT=10800`**: 3-hour timeout for large files
- **`NEPTUNE_CONNECT_TIMEOUT=10`**: Fast connection establishment

## 🧪 Testing Your Setup

Before running the full bulk load, test your cluster's concurrent limit:

```bash
# Test concurrent load capacity
python test_concurrent_limit.py
```

This will:
1. Test your cluster's concurrent load limit
2. Provide recommendations
3. Show the high-performance setup

## 📊 Performance Expectations

### Expected Improvements
- **Speed**: 3-5x faster than default mode
- **Throughput**: Up to 15 files processed simultaneously
- **Efficiency**: Optimized retry logic and queue management

### Monitoring
The bulk loader provides real-time progress updates:
```
Progress: 45.2% | Completed: 23 | Failed: 0 | Active: 15 | Pending: 12 | Retry: 0
```

## ⚠️ Important Considerations

### Cluster Capacity
- **Small Clusters**: May be overwhelmed by 15 concurrent loads
- **Medium Clusters**: Should handle this configuration well
- **Large Clusters**: Can potentially handle even more concurrent loads

### Resource Usage
- **CPU**: Higher CPU usage due to concurrent processing
- **Memory**: Increased memory usage for parallel operations
- **Network**: Higher network bandwidth requirements

### Error Handling
- Individual file failures won't stop the entire process
- Failed files are logged for review
- Retry logic handles temporary failures

## 🔍 Troubleshooting

### Common Issues

1. **Concurrent Limit Exceeded**
   ```
   Error: Max concurrent load limit breached
   ```
   **Solution**: Reduce `NEPTUNE_CONCURRENT_LIMIT` to a lower value

2. **Timeout Errors**
   ```
   Error: Load timeout after 10800 seconds
   ```
   **Solution**: Increase `NEPTUNE_TIMEOUT` for very large files

3. **Connection Issues**
   ```
   Error: Connection timeout
   ```
   **Solution**: Check network connectivity and cluster endpoint

### Debug Mode
Enable detailed logging for troubleshooting:
```bash
export NEPTUNE_DEBUG=true
python src/generate/gremlin/bulk_load_nodes_edges.py
```

## 📈 Performance Optimization Tips

1. **File Size**: Larger files benefit more from concurrent loading
2. **File Order**: Nodes are loaded before edges for better performance
3. **S3 Location**: Ensure files are in the same region as your Neptune cluster
4. **Network**: Use high-bandwidth connections for best performance

## 🔄 Reverting to Default Settings

To return to conservative settings:
```bash
unset NEPTUNE_ULTRA_MODE NEPTUNE_CONCURRENT_LIMIT
python src/generate/gremlin/bulk_load_nodes_edges.py
```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the logs with `NEPTUNE_DEBUG=true`
3. Test with a smaller `NEPTUNE_CONCURRENT_LIMIT`
4. Monitor your Neptune cluster's CloudWatch metrics

## 🎯 Best Practices

1. **Start Conservative**: Begin with a lower concurrent limit and increase gradually
2. **Monitor Resources**: Watch CPU, memory, and network usage
3. **Test First**: Always test with a subset of files before full deployment
4. **Backup**: Ensure you have backups before large bulk operations
5. **Schedule**: Run during off-peak hours for production clusters 