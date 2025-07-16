```
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