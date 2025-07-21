# Neptune Bulk Loader

## Setup

### 1. Environment Configuration

Before running the bulk loader, you need to set up your environment variables. The script uses a `.env` file for configuration.

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Edit the `.env` file and set the required variables:
   ```bash
   # Required variables
   S3_BUCKET=your-s3-bucket-name
   NEPTUNE_IAM_ROLE_ARN=arn:aws:iam::123456789012:role/NeptuneLoadFromS3
   
   # Optional variables
   NEPTUNE_ENDPOINT=https://localhost:8182
   AWS_REGION=us-east-1
   ```

### 2. Testing Environment Setup

Before running the bulk loader, you can test that your environment is configured correctly:

```bash
python test_env_loading.py
```

This will verify that your `.env` file is set up properly and all required variables are configured.

### 3. Running the Bulk Loader

The bulk loader script automatically loads environment variables from the `.env` file and manages concurrent loads for optimal performance.

```bash
python src/generate/gremlin/bulk_load_nodes_edges.py
```

## Manual Load Example

For manual loading using curl:

```bash
curl -k -X POST https://localhost:8182/loader \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3://deam-neptune/test.csv",
    "format": "csv",
    "iamRoleArn": "arn:aws:iam::244081531951:role/NeptuneLoadFromS3",
    "region": "us-east-1",
    "failOnError": "TRUE",
    "parallelism": "MEDIUM",
    "updateSingleCardinalityProperties": "FALSE",
    "queueRequest": "FALSE"
  }'
```

## Performance Modes

The bulk loader supports different performance modes:

- **Standard Mode**: Default configuration with balanced performance
- **High Performance Mode**: Set `NEPTUNE_PERFORMANCE_MODE=true` in your `.env` file
- **Ultra Performance Mode**: Set `NEPTUNE_ULTRA_MODE=true` in your `.env` file (use with caution)

## Environment Variables Reference

See the script's docstring for a complete list of available environment variables and their descriptions.
