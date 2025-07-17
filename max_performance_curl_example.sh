#!/bin/bash

# Single curl command for maximum performance Neptune bulk load
# Replace the S3 path and IAM role ARN with your actual values

# Example curl command for maximum performance:
curl -X POST \
  -H "Content-Type: application/json" \
  -k \
  "https://localhost:8182/loader" \
  -d '{
    "source": "s3://deam-neptune/",
    "format": "csv",
    "iamRoleArn": "arn:aws:iam::244081531951:role/NeptuneLoadFromS3",
    "region": "us-east-1",
    "failOnError": "FALSE",
    "parallelism": "OVERSUBSCRIBE",
    "queueRequest": "TRUE"
  }'

echo ""
echo "Maximum Performance Settings Used:"
echo "- parallelism: OVERSUBSCRIBE (maximum parallelism)"
echo "- failOnError: FALSE (continue on errors)"
echo "- queueRequest: TRUE (queue for high concurrency)"
echo ""
echo "To load multiple files, run this command for each file path:"
echo "- s3://deam-neptune/nodes/person_nodes.csv"
echo "- s3://deam-neptune/nodes/address_nodes.csv"
echo "- s3://deam-neptune/edges/person_address_edges.csv"
echo "- etc." 