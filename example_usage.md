# Neptune Bulk Load Concurrency Test - Usage Example

## Fixed SSL Issue

The script now automatically handles SSL certificate verification for localhost/tunneled connections. The SSL certificate verification error has been fixed.

## Prerequisites

1. **SSH Tunnel Setup**: Ensure you have an SSH tunnel running to Neptune
   ```bash
   python src/generate/utils/ssh_tunnel_start.py
   ```

2. **AWS Credentials**: Configure your AWS credentials for S3 access
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. **S3 Bucket**: Ensure you have an S3 bucket with test data or use the `--create-sample-data` flag

## Basic Usage

### For Localhost/Tunneled Connections (Automatically Fixed)

```bash
python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
    localhost \
    us-east-1 \
    your-s3-bucket \
    arn:aws:iam::123456789012:role/NeptuneBulkLoadRole \
    --create-sample-data \
    --max-concurrency 20 \
    --step 5
```

**Note**: The script now automatically detects localhost connections and enables insecure mode. You no longer need to manually add the `-k` flag.

### For Direct Neptune Connections

```bash
python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
    your-cluster.cluster-xxx.us-east-1.neptune.amazonaws.com \
    us-east-1 \
    your-s3-bucket \
    arn:aws:iam::123456789012:role/NeptuneBulkLoadRole \
    --create-sample-data \
    --max-concurrency 20
```

## Advanced Options

### Monitor Load Completion (Slower but More Comprehensive)

```bash
python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
    localhost \
    us-east-1 \
    your-s3-bucket \
    arn:aws:iam::123456789012:role/NeptuneBulkLoadRole \
    --create-sample-data \
    --monitor-completion \
    --max-concurrency 10
```

### Custom Parallelism Settings

```bash
python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
    localhost \
    us-east-1 \
    your-s3-bucket \
    arn:aws:iam::123456789012:role/NeptuneBulkLoadRole \
    --parallelism HIGH \
    --create-sample-data
```

### Custom Data Files

```bash
python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
    localhost \
    us-east-1 \
    your-s3-bucket \
    arn:aws:iam::123456789012:role/NeptuneBulkLoadRole \
    --create-sample-data \
    --data-files 20 \
    --records-per-file 5000
```

## What the Fix Does

1. **Automatic Detection**: Detects when endpoint is localhost or 127.0.0.1
2. **SSL Context Adjustment**: Automatically disables hostname verification for localhost connections
3. **No Interactive Prompts**: Removes the need for user input during execution
4. **Better Error Messages**: Provides specific error messages for SSL issues

## Expected Output

```
Detected localhost endpoint - this appears to be a tunnel setup.
Automatically enabling insecure mode (-k flag) for tunneled connections.
Starting Neptune bulk load concurrency test...
Endpoint: localhost:8182
S3 Bucket: your-s3-bucket
Max concurrency: 20
Parallelism: MEDIUM
Monitor completion: False
SSL verification: Disabled
Using 10 data files

Testing connection to Neptune...
✓ Successfully connected to Neptune endpoint

Testing bulk load concurrency level: 5
Testing bulk load concurrency level: 10
Testing bulk load concurrency level: 15
Testing bulk load concurrency level: 20
...
```

## Troubleshooting

### Still Getting SSL Errors?

1. **Check SSH Tunnel**: Ensure the tunnel is running
   ```bash
   python src/generate/utils/ssh_tunnel_check.py
   ```

2. **Test Basic Connection**: Use the simple test script
   ```bash
   python test_ssl_fix.py
   ```

3. **Manual SSL Disable**: If needed, you can still use the `-k` flag
   ```bash
   python src/generate/gremlin/tests/neptune_bulk_load_concurrency_test.py \
       localhost us-east-1 your-s3-bucket your-role-arn -k
   ```

### Other Common Issues

- **S3 Access**: Ensure your IAM role has S3 read permissions
- **Neptune Permissions**: Ensure your IAM role has Neptune bulk load permissions
- **Network Issues**: Check if your SSH tunnel is stable 