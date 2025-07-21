# Neptune Bulk Loader - Fixed Version

This document describes the fixes applied to the Neptune bulk loader script to resolve connection timeout issues.

## Issues Fixed

### 1. Connection Timeout Issues
- **Problem**: Default 60-second timeout was too short for Neptune bulk loader operations
- **Fix**: Increased default timeout to 300 seconds with separate connect timeout of 30 seconds
- **Environment Variable**: `NEPTUNE_TIMEOUT` (default: 300), `NEPTUNE_CONNECT_TIMEOUT` (default: 30)

### 2. No Retry Mechanism
- **Problem**: Script failed immediately on connection errors without retrying
- **Fix**: Added configurable retry logic with exponential backoff
- **Environment Variables**: `NEPTUNE_RETRY_ATTEMPTS` (default: 3), `NEPTUNE_RETRY_DELAY` (default: 5)

### 3. Poor Connection Pooling
- **Problem**: No connection pooling configuration for concurrent requests
- **Fix**: Added proper connection pooling with HTTPAdapter configuration
- **Benefit**: Better handling of concurrent connections and reduced connection overhead

### 4. No Health Check
- **Problem**: Script didn't verify Neptune endpoint accessibility before starting
- **Fix**: Added connection test during initialization
- **Benefit**: Early failure detection and better error messages

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEPTUNE_ENDPOINT` | `https://localhost:8182` | Neptune cluster endpoint |
| `NEPTUNE_IAM_ROLE_ARN` | (required) | IAM role ARN for S3 access |
| `AWS_REGION` | `us-east-1` | AWS region |
| `S3_BUCKET` | `deam-neptune` | S3 bucket containing CSV files |
| `NEPTUNE_MAX_WORKERS` | `10` | Maximum concurrent workers |
| `NEPTUNE_PARALLELISM` | `HIGH` | Neptune loader parallelism |
| `NEPTUNE_TIMEOUT` | `300` | Request timeout in seconds |
| `NEPTUNE_CONNECT_TIMEOUT` | `30` | Connection timeout in seconds |
| `NEPTUNE_RETRY_ATTEMPTS` | `3` | Number of retry attempts |
| `NEPTUNE_RETRY_DELAY` | `5` | Delay between retries in seconds |
| `NEPTUNE_FAIL_ON_ERROR` | `true` | Whether to fail on errors |
| `NEPTUNE_QUEUE_REQUEST` | `true` | Whether to queue requests |

## Usage

### 1. Test Connection First
Before running the bulk loader, test the connection:

```bash
# Set your Neptune endpoint
export NEPTUNE_ENDPOINT="https://your-neptune-cluster.cluster-xyz.us-east-1.neptune.amazonaws.com:8182"

# Test connection
python src/generate/utils/test_neptune_connection.py
```

### 2. Run Bulk Loader
```bash
# Set required environment variables
export NEPTUNE_ENDPOINT="https://your-neptune-cluster.cluster-xyz.us-east-1.neptune.amazonaws.com:8182"
export NEPTUNE_IAM_ROLE_ARN="arn:aws:iam::123456789012:role/NeptuneLoadFromS3"
export S3_BUCKET="your-s3-bucket-name"

# Run the bulk loader
python src/generate/utils/bulkload_neptune_all_files_s3-deam-neptune.py
```

### 3. Customize Timeouts and Retries
For slow connections or large files, you can increase timeouts:

```bash
export NEPTUNE_TIMEOUT=600  # 10 minutes
export NEPTUNE_CONNECT_TIMEOUT=60  # 1 minute
export NEPTUNE_RETRY_ATTEMPTS=5  # More retries
export NEPTUNE_RETRY_DELAY=10  # Longer delay between retries
```

## Troubleshooting

### Connection Timeout Errors
If you see connection timeout errors:

1. **Test connectivity first**:
   ```bash
   python src/generate/utils/test_neptune_connection.py
   ```

2. **Check network connectivity**:
   ```bash
   # Test basic connectivity
   ping your-neptune-cluster.cluster-xyz.us-east-1.neptune.amazonaws.com
   
   # Test port connectivity
   telnet your-neptune-cluster.cluster-xyz.us-east-1.neptune.amazonaws.com 8182
   ```

3. **Increase timeouts**:
   ```bash
   export NEPTUNE_CONNECT_TIMEOUT=60
   export NEPTUNE_TIMEOUT=600
   ```

4. **Check AWS credentials and permissions**:
   ```bash
   aws sts get-caller-identity
   ```

### Common Issues

1. **SSL Certificate Issues**: For localhost development, SSL verification is automatically disabled
2. **IAM Role Permissions**: Ensure the IAM role has S3 read access and Neptune write access
3. **Security Groups**: Verify Neptune security groups allow connections from your IP/network
4. **VPC Configuration**: Ensure proper VPC routing and subnet configuration

## Performance Tips

1. **Adjust worker count**: For large datasets, increase `NEPTUNE_MAX_WORKERS`
2. **Use appropriate parallelism**: `HIGH` for most cases, `LOW` for very large files
3. **Monitor memory usage**: Large concurrent loads may require more memory
4. **Batch processing**: Consider processing files in smaller batches for very large datasets

## Error Handling

The improved script provides:

- **Detailed error messages** with specific failure reasons
- **Retry logic** for transient connection issues
- **Progress tracking** with attempt counts
- **Comprehensive reporting** showing success/failure rates
- **Troubleshooting tips** when errors occur

## Monitoring

The script provides real-time progress updates and a final summary report including:

- Total files processed
- Success/failure counts
- Processing time
- Individual file status with retry attempts
- Data size information 